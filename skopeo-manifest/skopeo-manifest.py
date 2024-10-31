#!/usr/bin/env python3

"""
This script writes a Skopeo manifest for the given images.
"""

import argparse
import json
import os
import re
import sys

import yaml


def split_image(image):
    """
    Splits an image into registry, repository and tag.
    """
    image = image.rsplit("@", maxsplit = 1)[0]
    repository, tag, *unused = image.rsplit(":", maxsplit = 1) + [None]
    registry, repository, *unused = repository.split("/", maxsplit = 1) + [None]

    if repository is None:
        repository = f"library/{registry}"
        registry = "docker.io"
    if "." not in registry and ":" not in registry:
        repository = f"{registry}/{repository}"
        registry = "docker.io"
    if not tag:
        tag = "latest"

    return registry, repository, tag
    

def parse_images(images, format):
    """
    Parse the images using the specified format.
    """
    if format == "json":
        return json.loads(images)
    elif format == "newline":
        # We only return non-empty lines
        return [i.strip() for i in images.splitlines() if i.strip()]
    else:
        raise ValueError(f"unknown format - {format}")


def skopeo_manifest(images):
    """
    Produce the Skopeo manifest structure for the given images.
    """
    manifest = {}
    for registry, repository, tag in images:
        images = manifest.setdefault(registry, {}).setdefault("images", {})
        images.setdefault(repository, []).append(tag)
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description = "Extracts images from Kubernetes manifests in a file."
    )
    parser.add_argument(
        "--format",
        help = "The format that the images are given in.",
        choices = ["json", "newline"],
        default = "newline"
    )
    parser.add_argument("manifest_file", help = "The file to write the manifest to.")
    parser.add_argument("images", help = "The images to include in the manifest.")
    args = parser.parse_args()

    images = [split_image(image) for image in parse_images(args.images, args.format)]
    manifest = skopeo_manifest(sorted(images))

    with open(args.manifest_file, "w") as fh:
        yaml.safe_dump(manifest, fh)

    # Output the manifest file
    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
    with open(output_path, "a") as fh:
        print(f"manifest-file={args.manifest_file}", file = fh)


if __name__ == "__main__":
    main()
