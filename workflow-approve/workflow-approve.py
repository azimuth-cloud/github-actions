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


def get_pr(session, repo, number):
    response = session.get(f"{GITHUB_API}/repos/{repo}/pulls/{number}")
    response.raise_for_status()
    return response.json()


def create_pr_comment(session, pr, comment_text):
    response = session.post(pr["comments_url"], json = {"body": comment_text})
    response.raise_for_status()
    return response.json()


def wait_for_reactions(session, comment, approvers):
    # This function returns the list of reactions from approvers
    reactions_url = comment["reactions"]["url"]
    while True:
        response = session.get(reactions_url)
        response.raise_for_status()
        reactions = [
            reaction
            for reaction in response.json()
            if (
                reaction["content"] in {"+1", "-1"} and
                reaction["user"]["login"] in approvers
            )
        ]
        if reactions:
            return reactions
        else:
            time.sleep(30)


def is_approved(reactions):
    # If there is a -1, that takes precedence over any +1s
    denied_by = next(
        (
            reaction["user"]["login"]
            for reaction in reactions
            if reaction["content"] == "-1"
        ),
        None
    )
    if denied_by:
        return False, denied_by
    approved_by = next(
        (
            reaction["user"]["login"]
            for reaction in reactions
            if reaction["content"] == "+1"
        ),
        None
    )
    if approved_by:
        return True, approved_by
    raise RuntimeError("could not find +1 or -1 reaction")


def update_pr_comment(session, comment, next_comment_text):
    response = session.patch(comment["url"], json = {"body": next_comment_text})
    response.raise_for_status()
    return response.json()


class CommaSeparatedListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        setattr(namespace, self.dest, [v.strip() for v in values.split(",")])


def main():
    parser = argparse.ArgumentParser(
        description = (
            "Ensures that a workflow has received the required approval before proceeding."
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
        "--approval-required",
        help = "Indicates whether approval is required for the workflow run (default true).",
        action = argparse.BooleanOptionalAction,
        default = True
    )
    parser.add_argument(
        "repo",
        help = "The name of the repo containing the PR that triggered the current workflow run."
    )
    parser.add_argument(
        "pr_number",
        help = "The number of the PR that triggered the current workflow run.",
        type = int
    )
    parser.add_argument(
        "run_id",
        help = "The ID of the current workflow run.",
        type = int
    )
    parser.add_argument(
        "approvers",
        help = "Comma-separated list of approvers for the workflow run.",
        action = CommaSeparatedListAction
    )
    args = parser.parse_args()


    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {args.token}",
    })

    if not args.approval_required:
        print(
            f"[INFO] no approval required for workflow run {args.run_id} "
            f"for PR {args.pr_number} - exiting"
        )
        return

    print(f"[INFO] fetching details for PR {args.pr_number}")
    pr = get_pr(session, args.repo, args.pr_number)

    print(f"[INFO] creating comment on PR {pr['number']} for run ID {args.run_id}")
    run_link = f"https://github.com/{args.repo}/actions/runs/{args.run_id}"
    comment = create_pr_comment(
        session,
        pr,
        "\n".join([
            " ".join(f"@{approver}" for approver in args.approvers),
            "",
            f"Approval is required for [workflow run #{args.run_id}]({run_link}) for this PR.",
            "",
            (
                "Please review the code that will be executed by this workflow run "
                "and give either a :thumbsup: or :thumbsdown: on this comment to "
                "approve or deny execution."
            ),
        ])
    )

    print(f"[INFO] waiting for reaction(s) on PR comment from {', '.join(args.approvers)}")
    reactions = wait_for_reactions(session, comment, args.approvers)

    print(f"[INFO] making decision based on reactions")
    approved, approver = is_approved(reactions)

    print(f"[INFO] updating PR comment with approval information")
    update_pr_comment(
        session,
        comment,
        "\n".join([
            comment["body"],
            "",
            f"**Workflow run {'approved' if approved else 'denied'} by {approver}.**"
        ])
    )

    if approved:
        print(f"[INFO] workflow run {args.run_id} approved by {approver}")
    else:
        print(f"[WARN] workflow run {args.run_id} denied by {approver}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
