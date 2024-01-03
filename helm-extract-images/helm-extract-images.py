#!/usr/bin/env python3

"""
This script attempts to locate images in the output of a Helm chart.
"""

import argparse
import json
import os
import subprocess

import yaml


def extract_images_chart_values(repo, name, version):
    """
    Attempts to extract images from the chart values.
    """
    # For any images we find that don't have a tag, assume the appVersion
    # To do that, we need to get the appVersion
    output = subprocess.check_output(
        [
            "helm",
            "show",
            "chart",
            name,
            "--repo",
            repo,
            "--version",
            version,
        ]
    )
    chart_info = yaml.safe_load(output)
    app_version = chart_info.get("appVersion", chart_info["version"])

    # The convention for specifying images in Helm charts is objects with repository and tag keys
    # Sometimes, registry is also used
    # So we look for objects like that and treat them as images
    def find_images(obj):
        if isinstance(obj, dict):
            if "repository" in obj and "tag" in obj:
                if "registry" in obj:
                    repository = "/".join([obj["registry"], obj["repository"]])
                else:
                    repository = obj["repository"]
                tag = obj["tag"] or app_version
                yield f"{repository}:{tag}"
            for value in obj.values():
                yield from find_images(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from find_images(value)

    # Fetch the values and locate the images within them
    # Return the result as a set to remove duplicates
    output = subprocess.check_output(
        [
            "helm",
            "show",
            "values",
            name,
            "--repo",
            repo,
            "--version",
            version,
        ]
    )
    return set(find_images(yaml.safe_load(output)))


def extract_images_template(repo, name, version, values):
    """
    Attempts to extract images from the rendered templates.
    """
    # Look for images in workloads, i.e. in the image field of a container spec
    def find_images(obj):
        if isinstance(obj, dict):
            if "image" in obj:
                yield obj["image"]
            for value in obj.values():
                yield from find_images(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from find_images(value)

    # Render the manifests using the given values and extract the images
    # Return the result as a set to remove duplicates
    output = subprocess.check_output(
        [
            "helm",
            "template",
            name,
            name,
            "--skip-tests",
            "--repo",
            repo,
            "--version",
            version,
            "--values",
            "-",
        ],
        input = values
    )
    return set(find_images(list(yaml.safe_load_all(output))))


def main():
    parser = argparse.ArgumentParser(
        description = "Attempts to locate images in the output of a Helm chart."
    )
    parser.add_argument("chart_repo", help = "The URL of the Helm repo.")
    parser.add_argument("chart_name", help = "The name of the chart.")
    parser.add_argument("chart_version", help = "The version of the chart.")
    parser.add_argument("values", help = "The values to use when rendering the chart.")
    args = parser.parse_args()

    print(
        f"[INFO ] searching for images in chart {args.chart_name} "
        f"from {args.chart_repo} at {args.chart_version}"
    )

    # First, look for images in the chart values.yaml
    print(f"[INFO ]   extracting images from chart values")
    images = extract_images_chart_values(
        args.chart_repo,
        args.chart_name,
        args.chart_version
    )

    print(f"[INFO ]   extracting images from templated manifests")
    # Add the images to the images we found above
    images.update(
        extract_images_template(
            args.chart_repo,
            args.chart_name,
            args.chart_version,
            args.values
        )
    )

    # Output the images as a JSON-formatted list
    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
    with open(output_path, "a") as fh:
        print(f"images={json.dumps(list(sorted(images)))}", file = fh)


if __name__ == "__main__":
    main()
