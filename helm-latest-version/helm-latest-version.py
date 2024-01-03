#!/usr/bin/env python3

"""
This script outputs the latest version for a Helm chart, optionally matching
a set of constraints.
"""

import argparse
import os

import requests
import yaml

import easysemver


def main():
    parser = argparse.ArgumentParser(
        description = "Gets the latest version of a Helm chart, optionally subject to constraints."
    )
    parser.add_argument("repo_url", help = "The URL of the Helm repo.")
    parser.add_argument("chart_name", help = "The name of the chart.")
    parser.add_argument(
        "constraints",
        help = "Comma-separated list of constraints to apply when considering versions."
    )
    args = parser.parse_args()

    print(f"[INFO ] fetching repository index from {args.repo_url}")
    response = requests.get(f"{args.repo_url}/index.yaml")
    response.raise_for_status()

    print(f"[INFO ] extracting versions for chart {args.chart_name}")
    entries = yaml.safe_load(response.content)["entries"][args.chart_name]

    # Find the most recent version that matches the constraints
    print(f"[INFO ] searching for versions matching {args.constraints}")
    version_range = easysemver.Range(args.constraints)
    latest_version = None
    latest_app_version = None
    for entry in entries:
        try:
            version = easysemver.Version(entry["version"])
        except TypeError:
            print(f"[WARN ] ignoring invalid version - {entry['version']}")
            continue
        if version not in version_range:
            continue
        if latest_version is None or version > latest_version:
            latest_version = version
            latest_app_version = entry.get("appVersion")

    if latest_version:
        print(f"[INFO ] found version - {latest_version}")
    else:
        print(f"[ERROR] no version matching constraints")
        raise SystemExit(1)

    # Output the next version so it can be consumed by later steps
    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
    with open(output_path, "a") as fh:
        print(f"version={latest_version}", file = fh)
        if latest_app_version:
            print(f"app_version={latest_app_version}", file = fh)


if __name__ == "__main__":
    main()
