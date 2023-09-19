#!/usr/bin/env python3

"""
This script outputs the latest release for a GitHub repository.
"""

import argparse
import os
import re
import urllib.parse

import requests


def main():
    parser = argparse.ArgumentParser(
        description = "Gets the latest release in a GitHub repository."
    )
    parser.add_argument("repo", help = "The GitHub repo to get releases from.")
    args = parser.parse_args()

    # If we have been given a full URL to a repository, get the repository name
    if re.search("^https?://", args.repo) is not None:
        print(f"[INFO] extracting repo name from {args.repo}")
        repo = urllib.parse.urlsplit(args.repo).path.removeprefix("/")
    else:
        repo = args.repo

    print(f"[INFO] fetching latest release for {repo}")
    response = requests.get(f"https://api.github.com/repos/{repo}/releases/latest")
    response.raise_for_status()

    print(f"[INFO] extracting tag name")
    version = response.json()["tag_name"].split("/", maxsplit = 1)[-1]

    print(f"[INFO] found version - {version}")

    # Output the next version so it can be consumed by later steps
    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
    with open(output_path, "a") as fh:
        print(f"version={version}", file = fh)


if __name__ == "__main__":
    main()
