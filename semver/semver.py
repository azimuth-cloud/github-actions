#!/usr/bin/env python3

"""
This script generates a SemVer-compatible version for the current commit using a combination
of the last tag, the distance from that tag and the name of the branch that the commit is on.

The version is constructed such that the versions for a particular branch will order correctly.

It is assumed that tags are SemVer compliant, i.e. `<major>.<minor>.<patch>-<prerelease>`.

It also returns a short-sha as a secondary output.
"""

import os
import re
import subprocess
import sys


def cmd(command):
    """
    Execute the given command and return the output.
    """
    output = subprocess.check_output(command, text = True, stderr = subprocess.DEVNULL)
    return output.strip()


#: Regex that attempts to match a SemVer version
#: It allows the tag to maybe start with a "v"
SEMVER_REGEX = r"^v?(?P<major>[0-9]+).(?P<minor>[0-9]+).(?P<patch>[0-9]+)(-(?P<prerelease>[a-zA-Z0-9.-]+))?$"


def get_version():
    """
    Returns a (version, short_sha) tuple where version is a SemVer-compliant version based on
    Git information for the current working directory.
    """
    full_sha = cmd(["git", "log", "-1", "--format=%H"])
    # The short SHA is just the first seven characters
    short_sha = full_sha[:7]
    # Deriving the semver version is more tricky
    try:
        # Start by trying to find the most recent tag
        last_tag = cmd(["git", "describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        # If there are no tags, then set the parts in such a way that when we increment the patch version we get 0.1.0
        major_vn = 0
        minor_vn = 1
        patch_vn = -1
        prerelease_vn = None
        # Since there is no tag, just count the number of commits in the branch
        commits = int(cmd(["git", "rev-list", "--count", "HEAD"]))
    else:
        # If we found a tag, split into major/minor/patch/prerelease
        tag_bits = re.search(SEMVER_REGEX, last_tag)
        if tag_bits is None:
            raise RuntimeError(f'Tag is not a valid SemVer version - {last_tag}')
        major_vn = int(tag_bits.group('major'))
        minor_vn = int(tag_bits.group('minor'))
        patch_vn = int(tag_bits.group('patch'))
        prerelease_vn = tag_bits.group('prerelease')
        # Get the number of commits since the last tag
        commits = int(cmd(["git", "rev-list", "--count", f"{last_tag}..HEAD"]))

    if commits > 0:
        # If there are commits since the last tag and no existing prerelease part, increment the patch version
        if not prerelease_vn:
            patch_vn += 1
        # Add information to the prerelease part about the branch and number of commits
        event_name = os.environ["GITHUB_EVENT_NAME"]
        is_pull_request = event_name in {"pull_request", "pull_request_target"}
        if is_pull_request:
            branch_name = os.environ["GITHUB_HEAD_REF"]
        else:
            branch_name = os.environ["GITHUB_REF_NAME"]
        # Sanitise the branch name so it only has characters valid for a prerelease version
        branch_name = re.sub("[^a-zA-Z0-9-]+", "-", branch_name).strip("-").lower()
        prerelease_vn = '.'.join([prerelease_vn or "dev.0", branch_name, str(commits)])

    # Build the SemVer version from the parts
    version = f"{major_vn}.{minor_vn}.{patch_vn}"
    if prerelease_vn:
        version += f"-{prerelease_vn}"

    return version, full_sha, short_sha


def main():
    """
    Entrypoint for the script.
    """
    version, full_sha, short_sha = get_version()
    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
    with open(output_path, "a") as fh:
        print(f"version={version}", file = fh)
        print(f"full-sha={full_sha}", file = fh)
        print(f"short-sha={short_sha}", file = fh)


if __name__ == "__main__":
    main()
