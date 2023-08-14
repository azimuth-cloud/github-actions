#!/usr/bin/env python3

"""
This script publishes the Helm charts from the given directory with the
given version and appVersion.
"""

import base64
import contextlib
import functools
import pathlib
import os
import subprocess
import tempfile

import yaml


@contextlib.contextmanager
def working_directory(directory):
    """
    Context manager that runs the wrapped code with the given directory as the
    working directory.

    When the context manager exits, the original working directory is restored.
    """
    previous_cwd = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(previous_cwd)


def cmd(command):
    """
    Execute the given command and return the output.
    """
    output = subprocess.check_output(command, text = True)
    return output.strip()


def chart_directory_cmp(chart_directories):
    """
    Returns a sorting function for the chart directories.
    """
    # First, assemble the first-order dependencies from the chart files
    dependencies = {}
    for chart_directory in chart_directories:
        with open(chart_directory / "Chart.yaml") as f:
            chart_info = yaml.safe_load(f)
            dependencies[chart_directory] = set(
                d
                for d in [
                    (chart_directory / dep["repository"].removeprefix("file://")).resolve()
                    for dep in chart_info.get("dependencies", [])
                    if dep["repository"].startswith("file://")
                ]
                if d in chart_directories
            )
    # Then resolve the recursive dependencies
    # Define a function to recursively resolve dependencies for a given directory
    def resolve_dependencies(chart_directory):
        for dependency in dependencies[chart_directory]:
            yield dependency
            yield from dependencies[dependency]
    def cmp(first, second):
        if first in resolve_dependencies(second):
            return -1
        elif second in resolve_dependencies(first):
            return 1
        else:
            return 0
    return cmp


def sort_chart_directories(chart_directories):
    """
    Sort the chart directories into the order in which they need to have their
    dependencies updated in order to respect local dependencies.
    """
    sort_key = functools.cmp_to_key(chart_directory_cmp(chart_directories))
    return sorted(chart_directories, key = sort_key)


class quoted_str(str):
    """
    Subclass of str for marking strings that should always be rendered with quotes in YAML.

    This is required because PyYAML renders strings like '4214e07' without quotes, causing
    them to be treated as exponential-format integers when read back.
    """


def quoted_str_representer(dumper, data):
    """
    YAML representer for the quoted_str class.
    """
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style = '"')


yaml.add_representer(quoted_str, quoted_str_representer, Dumper = yaml.SafeDumper)


def update_chart_file(chart_directory, version, app_version):
    """
    Updates the Chart.yaml file for the given directory with the given version and appVersion.
    """
    chart_file = chart_directory / "Chart.yaml"
    with chart_file.open() as f:
        content = yaml.safe_load(f)
    # Ensure that version and appVersion are always rendered with quotes
    if version:
        content["version"] = quoted_str(version)
    if app_version:
        content["appVersion"] = quoted_str(app_version)
    with chart_file.open("w") as f:
        yaml.safe_dump(content, f)


def setup_publish_branch(branch, publish_directory):
    """
    Clones the specified branch into the specified directory.
    """
    server_url = os.environ["GITHUB_SERVER_URL"]
    repository = os.environ["GITHUB_REPOSITORY"]
    remote = f"{server_url}/{repository}.git"
    print(f"[INFO] Cloning {remote}@{branch} into {publish_directory}")
    # Try to clone the branch
    # If it fails, create a new empty git repo with the same remote
    try:
        cmd([
            "git",
            "clone",
            "--depth=1",
            "--single-branch",
            "--branch",
            branch,
            remote,
            publish_directory
        ])
    except subprocess.CalledProcessError:
        with working_directory(publish_directory):
            cmd(["git", "init"])
            cmd(["git", "remote", "add", "origin", remote])
            cmd(["git", "checkout", "--orphan", branch])
    username = os.environ["GITHUB_ACTOR"]
    email = f"{username}@users.noreply.github.com"
    with working_directory(publish_directory):
        print(f"[INFO] Configuring git to use username '{username}'")
        cmd(["git", "config", "user.name", username])
        cmd(["git", "config", "user.email", email])
        print("[INFO] Configuring git to use authentication token")
        # Basic auth credentials should be base64-encoded
        basic_auth = f"x-access-token:{os.environ['GITHUB_TOKEN']}"
        cmd([
            "git",
            "config",
            "http.extraheader",
            f"Authorization: Basic {base64.b64encode(basic_auth.encode()).decode()}"
        ])


def main():
    """
    Entrypoint for the script.
    """
    # Get the directory to publish charts from
    chart_directory = pathlib.Path(os.environ.get("CHART_DIRECTORY") or  ".").resolve()

    # Get the versions to use for the deployed charts
    version = os.environ.get("VERSION")
    app_version = os.environ.get("APP_VERSION")

    # Get the chart directories for the Helm charts under the given directory, ordered
    # so that dependencies are updated in the correct order
    chart_directories = sort_chart_directories([
        chart_file.parent
        for chart_file in chart_directory.glob("**/Chart.yaml")
    ])

    # Publish the charts and re-generate the repository index
    publish_branch = os.environ.get("PUBLISH_BRANCH") or "gh-pages"
    print(f"[INFO] Chart(s) will be published to branch '{publish_branch}'")
    if version:
        print(f"[INFO] Chart(s) will be published with version '{version}'")
    if app_version:
        print(f"[INFO] Chart(s) will be published with appVersion '{app_version}'")
    with tempfile.TemporaryDirectory() as publish_directory:
        setup_publish_branch(publish_branch, publish_directory)
        for chart_directory in chart_directories:
            if version or app_version:
                update_chart_file(chart_directory, version, app_version)
            print(f"[INFO] Updating dependencies for {chart_directory}")
            cmd(["helm", "dependency", "update", chart_directory])
            print(f"[INFO] Packaging chart in {chart_directory}")
            cmd(["helm", "package", "--destination", publish_directory, chart_directory])
        # Re-index the publish directory
        print("[INFO] Generating Helm repository index file")
        cmd(["helm", "repo", "index", publish_directory])
        with working_directory(publish_directory):
            print("[INFO] Committing changed files")
            cmd(["git", "add", "-A"])
            cmd(["git", "commit", "-m", f"Publishing charts for {version}"])
            print(f"[INFO] Pushing changes to branch '{publish_branch}'")
            cmd(["git", "push", "--set-upstream", "origin", publish_branch])


if __name__ == "__main__":
    main()
