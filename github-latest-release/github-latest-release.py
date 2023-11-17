#!/usr/bin/env python3

"""
This script outputs the latest release for a GitHub repository.
"""

import argparse
import os
import re
import urllib.parse

import requests

import easysemver


def github_session(token):
    """
    Initialises a requests session for interacting with GitHub.
    """
    session = requests.Session()
    session.headers["Content-Type"] = "application/json"
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def github_fetch_list(session, url):
    """
    Generator that yields items from paginating a GitHub URL.
    """
    next_url = url
    while next_url:
        response = session.get(next_url)
        response.raise_for_status()
        yield from response.json()
        next_url = response.links.get("next", {}).get("url")


def get_latest_release(session, repo, prereleases):
    """
    Gets the latest release for a repo using the releases API.

    If prereleases = True, the first release is returned.
    If prereleases = False, the release flagged as latest is returned.
    """
    if prereleases:
        release = next(github_fetch_list(session, f"https://api.github.com/repos/{repo}/releases"))
    else:
        response = session.get(f"https://api.github.com/repos/{repo}/releases/latest")
        response.raise_for_status()
        release = response.json()

    print(f"[INFO] extracting tag name")
    return release["tag_name"].split("/", maxsplit = 1)[-1]


def get_latest_tag(session, repo, prereleases):
    """
    Gets the latest tag for a repo using the tags API, for repositories
    that are not using releases properly.

    Tag names must be valid SemVer versions. Versions with a prerelease part are
    considered only when prereleases = True.
    """
    for tag in github_fetch_list(session, f"https://api.github.com/repos/{repo}/tags"):
        try:
            version = easysemver.Version(tag["name"])
        except TypeError:
            continue
        if prereleases or not version.prerelease:
            return tag["name"]
    raise RuntimeError("unable to find a suitable tag")


def main():
    parser = argparse.ArgumentParser(
        description = "Gets the latest release in a GitHub repository."
    )
    # Allow the token to come from an environment variable
    # We use this particular form so that the empty string becomes None
    env_token = os.environ.get("GITHUB_TOKEN") or None
    parser.add_argument(
        "--token",
        help = "The GitHub token to use (can be set using GITHUB_TOKEN envvar).",
        default = env_token,
        required = False
    )
    parser.add_argument(
        "--prereleases",
        help = "Indicates whether pre-releases should be included.",
        action = argparse.BooleanOptionalAction,
        default = False
    )
    parser.add_argument(
        "--tags",
        help = "Indicates whether to use tags or releases.",
        action = argparse.BooleanOptionalAction,
        default = False
    )
    parser.add_argument("repo", help = "The GitHub repo to get releases from.")
    args = parser.parse_args()

    session = github_session(args.token)

    # If we have been given a full URL to a repository, get the repository name
    if re.search("^https?://", args.repo) is not None:
        print(f"[INFO] extracting repo name from {args.repo}")
        repo = urllib.parse.urlsplit(args.repo).path.removeprefix("/")
    else:
        repo = args.repo

    if args.prereleases:
        print(f"[INFO] prereleases will be considered")

    if args.tags:
        print(f"[INFO] getting latest version from tags")
        version = get_latest_tag(session, repo, args.prereleases)
    else:
        print(f"[INFO] getting latest version from releases")
        version = get_latest_release(session, repo, args.prereleases)

    print(f"[INFO] found version - {version}")

    # Output the next version so it can be consumed by later steps
    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
    with open(output_path, "a") as fh:
        print(f"version={version}", file = fh)


if __name__ == "__main__":
    main()
