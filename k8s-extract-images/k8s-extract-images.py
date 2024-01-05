#!/usr/bin/env python3

"""
This script attempts to locate images in a set of Kubernetes manifests.
"""

import json
import os
import re
import sys

import requests
import yaml


IMAGE_REGEX = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9./-]*:[a-zA-Z0-9_.-]+")


# This is a map of (api_group, kind) tuples to extractors
EXTRACTORS = {}


def image_extractor(api_group, kind):
    """
    Decorator that registers an image extractor for the specified kind.
    """
    def decorator(func):
        EXTRACTORS[(api_group, kind)] = func
        return func
    return decorator


def extract_images(obj):
    """
    Yields images for the given Kubernetes object.
    """
    if not isinstance(obj, dict):
        return
    api_version = obj.get("apiVersion")
    if not api_version:
        return
    if "/" in api_version:
        api_group = api_version.split("/")[0]
    else:
        api_group = ""
    try:
        extractor = EXTRACTORS[(api_group, obj["kind"])]
    except KeyError:
        return
    else:
        yield from extractor(obj)


def extract_images_regex(obj):
    """
    Yields images extracted by applying a regex.
    """
    if isinstance(obj, dict):
        for value in obj.values():
            yield from extract_images_regex(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from extract_images_regex(value)
    elif isinstance(obj, str):
        match = IMAGE_REGEX.search(obj)
        if match is not None:
            yield match.group(0)


def extract_images_container(container):
    """
    Yields the images for a container.
    """
    yield container["image"]
    # Search for images in the args and environment vars
    yield from extract_images_regex(container.get("args"))
    yield from extract_images_regex(container.get("env"))


@image_extractor("", "Pod")
def extract_images_pod(pod):
    """
    Yields the images for a pod.
    """
    for container in pod["spec"].get("initContainers", []):
        yield from extract_images_container(container)
    for container in pod["spec"]["containers"]:
        yield from extract_images_container(container)


@image_extractor("apps", "Deployment")
@image_extractor("apps", "StatefulSet")
@image_extractor("apps", "DaemonSet")
@image_extractor("batch", "Job")
def extract_images_workload(workload):
    """
    Yields the images for a workload that has a pod template.
    """
    yield from extract_images_pod(workload["spec"]["template"])


@image_extractor("batch", "CronJob")
def extract_images_cronjob(cronjob):
    """
    Yields the images for a CronJob.
    """
    yield from extract_images_workload(cronjob["spec"]["jobTemplate"])


@image_extractor("monitoring.coreos.com", "Alertmanager")
@image_extractor("monitoring.coreos.com", "Prometheus")
def extract_images_monitoring(obj):
    """
    Yields the images for a monitoring resource.
    """
    if "image" in obj["spec"]:
        yield obj["spec"]["image"]


@image_extractor("nvidia.com", "ClusterPolicy")
@image_extractor("mellanox.com", "NicClusterPolicy")
def extract_images_nvidia_clusterpolicy(clusterpolicy):
    """
    Extracts the images used for an NVIDIA GPU operator ClusterPolicy object or
    a Mellanox NicClusterPolicy object.
    """
    # The NVIDIA cluster policy objects contain a bunch of components that specify
    # their images using the keys "repository", "image" and "version"
    def find_images(obj):
        if isinstance(obj, dict):
            repository = obj.get("repository")
            image = obj.get("image")
            version = obj.get("version")
            if repository and image and version:
                yield f"{repository}/{image}:{version}"
            for value in obj.values():
                yield from find_images(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from find_images(value)
    
    yield from find_images(clusterpolicy)


def normalise_image(image):
    """
    Normalises an image by removing any SHA part and adding a registry if missing.
    """
    # Split the image into registry, repository and tag, discarding any SHAs
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

    return f"{registry}/{repository}:{tag}"


REGISTRY_HEADERS = {
    "Accept": ",".join([
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.oci.image.index.v1+json",
    ]),
}

def verify_image(image):
    """
    Verifies that an image exists.
    """
    # We know that we have a normalised image, so we can assume it has a registry and a tag
    repository, tag = image.rsplit(":", maxsplit = 1)
    registry, repository = repository.split("/", maxsplit = 1)

    # docker.io is not itself a valid Docker v2 registry
    if registry == "docker.io":
        registry = "registry-1.docker.io"

    manifest_url = f"https://{registry}/v2/{repository}/manifests/{tag}"
    # Attempt to get the manifest
    response = requests.get(manifest_url, headers = REGISTRY_HEADERS)
    # Some registries allow anonymous access, in which case we are done
    # Others return a 401, in which case we must fetch a token and re-request
    if response.status_code == 401:
        # Extract details from the WWW-Authenticate header about how to fetch a token
        auth_params = {}
        for key in ("realm", "service", "scope"):
            match = re.search(f"{key}=\"([^\"]*)\"", response.headers['www-authenticate'])
            if match is not None:
                auth_params[key] = match.group(1)
        # The realm must be present
        try:
            realm = auth_params.pop("realm")
        except KeyError:
            print(f"[WARN] unable to find auth realm for {image}", file = sys.stderr)
            return False
        response = requests.get(realm, params = auth_params)
        response.raise_for_status()
        token = response.json()['token']
        authorization_header = f'Bearer {token}'
        # Fetch the manifest using the token
        response = requests.get(
            manifest_url,
            headers = {
                **REGISTRY_HEADERS,
                "Authorization": authorization_header,
            }
        )
    if response.ok:
        return True
    else:
        return False


def main():
    images = set()

    for obj in yaml.safe_load_all(os.environ["MANIFESTS"]):
        for image in extract_images(obj):
            image = normalise_image(image)
            print(f"[INFO] found image - {image}")
            if verify_image(image):
                images.add(image)
            else:
                print(f"[WARN]   image failed verification")

    # Output the images as a JSON-formatted list
    output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
    with open(output_path, "a") as fh:
        print(f"images={json.dumps(sorted(list(images)))}", file = fh)


if __name__ == "__main__":
    main()
