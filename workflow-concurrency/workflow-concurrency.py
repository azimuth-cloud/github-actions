#!/usr/bin/env python3

"""
This script imposes concurrency constraints on workflow runs that are too complex
to be expressed with the native concurrency controls.
"""

import argparse
import os
import time

import requests


GITHUB_API = "https://api.github.com"


def workflow_runs(session, repo, workflow_id, **params):
    """
    Returns the workflow runs with the specified status.
    """
    url = f"{GITHUB_API}/repos/{repo}/actions/workflows/{workflow_id}/runs"
    while url:
        response = session.get(url, params = params)
        response.raise_for_status()
        yield from response.json()["workflow_runs"]
        url, params = response.links.get("next", {}).get("url"), None


def cancel_existing_runs(session, current_run):
    """
    Cancel any in-progress runs for the same branch with a lower run_number than the current run.
    """
    in_progress = workflow_runs(
        session,
        current_run["repository"]["full_name"],
        current_run["workflow_id"],
        status = "in_progress",
        # We only want to cancel runs for the same branch
        branch = current_run["head_branch"]
    )
    for run in in_progress:
        if run["run_number"] >= current_run["run_number"]:
            continue
        print(f"[INFO]   cancelling run #{run['run_number']}")
        response = session.post(
            "{}/repos/{}/actions/runs/{}/cancel".format(
                GITHUB_API,
                run["repository"]["full_name"],
                run["id"]
            )
        )
        # A 409 indicates that the run is already stopped
        if response.status_code not in {202, 409}:
            response.raise_for_status()


def wait_for_slot(session, current_run, max_concurrency):
    """
    Waits for a free slot, given the maximum permitted concurrency.
    """
    while True:
        # Get all the in-progress runs for the same workflow, for any branch
        # We sort them by run number from low to high
        # Note that this is guaranteed to have at least one job in - us!
        in_progress = sorted(
            (
                run["run_number"]
                for run in workflow_runs(
                    session,
                    current_run["repository"]["full_name"],
                    current_run["workflow_id"],
                    status = "in_progress"
                )
            )
        )
        # Find our index within the running jobs
        try:
            current_idx = in_progress.index(current_run["run_number"])
        except ValueError:
            print(
                "[WARN]   "
                f"current run (#{current_run['run_number']}) "
                "not present in in-progress list - retrying"
            )
            time.sleep(60)
            continue
        # If we are within the max concurrency of the front of the queue, we can run
        if current_idx < max_concurrency:
            break
        # Otherwise, we wait
        print(f"[INFO]   waiting for {current_idx - max_concurrency + 1} run(s) to complete")
        # The rate limit for tokens issued to actions is 1000 requests per repo per hour
        # We want to make sure that between all the waiting jobs we don't exceed that
        if current_idx == max_concurrency:
            # We are the next job in the queue
            # Wait for 1m so that we start quickly after the previous job completes
            time.sleep(60)
        else:
            # We want to make sure that between the remaining jobs we don't exceed the limit
            # The next job will consume ~60 requests per hour with a fast wait
            # Other jobs might also make requests, so assume we have 500 req/repo/hr to play with
            waiting_not_first = len(in_progress) - max_concurrency - 1
            time.sleep(max(waiting_not_first * (3600 / 500), 60))


def main():
    parser = argparse.ArgumentParser(
        description = (
            "Updates the version of a release artefact in a GitHub repository "
            "to the latest release."
        )
    )
    # Allow the token to come from an environment variable
    # We use this particular form so that the empty string becomes None
    env_token = os.environ.get("GITHUB_TOKEN") or None
    parser.add_argument(
        "--token",
        help = "The GitHub token to use (can be set using GITHUB_TOKEN envvar).",
        default = env_token,
        required = env_token is None
    )
    parser.add_argument(
        "--max-concurrency",
        help = "The maximum number of concurrent workflow runs for the workflow.",
        type = int,
        default = 1
    )
    parser.add_argument(
        "--cancel",
        help = "Cancel existing runs for the same workflow and branch (default true).",
        action = "store_true",
        default = True
    )
    parser.add_argument(
        "--no-cancel",
        help = "Do not cancel existing runs for the same workflow and branch.",
        dest = "cancel",
        action = "store_false",
        default = argparse.SUPPRESS
    )
    parser.add_argument("repo", help = "The name of the repo that we are operating on.")
    parser.add_argument("run_id", help = "The ID of the current workflow run.", type = int)
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {args.token}",
    })

    # Get the details of this run
    print(f"[INFO] fetching details for run {args.run_id}")
    response = session.get(f"{GITHUB_API}/repos/{args.repo}/actions/runs/{args.run_id}")
    response.raise_for_status()
    current_run = response.json()
    print(f"[INFO] found run number #{current_run['run_number']}")
    # Currently, we only support the pull_request event
    if current_run["event"] != "pull_request":
        raise RuntimeError("only the pull_request event is currently supported")
    # We should be an in-progress run
    if current_run["status"] != "in_progress":
        raise RuntimeError(f"run {args.run_id} is not in-progress")
    
    # Cancel any in-progress runs that are superseded by this run, if requested
    if args.cancel:
        print(f"[INFO] cancelling runs superseded by #{current_run['run_number']}")
        cancel_existing_runs(session, current_run)

    # Wait for a slot to become available for this run
    print(f"[INFO] waiting for slot to become available")
    wait_for_slot(session, current_run, args.max_concurrency)
    print(f"[INFO] slot is available - exiting")


if __name__ == "__main__":
    main()
