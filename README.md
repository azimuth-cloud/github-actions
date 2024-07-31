# github-actions

This repository contains common GitHub Actions that are shared between multiple Azimuth repositories.

## Available actions

Currently, the available actions are:

| Name | Description |
|---|---|
| [config-extract](./config-extract) | Extract values from a structured config file. |
| [config-update](./config-update) | Update values in a structured config file. |
| [docker-multiarch-build-push](./docker-multiarch-build-push) | Build, scan and optionally push a multi-architecture Docker image. |
| [generate-app-token](./generate-app-token) | Generates app tokens for performing privileged operations. |
| [github-latest-release](./github-latest-release) | Fetches the latest release for a GitHub repository. |
| [helm-latest-version](./helm-latest-version) | Fetches the latest version for a Helm chart. |
| [helm-publish](./helm-publish) | Publish the Helm charts from the given directory to another branch in the repository (e.g. `gh-pages`). |
| [helm-template](./helm-template) | Template the manifests for a Helm chart. |
| [k8s-extract-images](./k8s-extract-images) | Extract the required images from a set of Kubernetes manifests. |
| [semver](./semver) | Generate a [SemVer](https://semver.org/) compatible version for the current commit. |
| [skopeo-manifest](./skopeo-manifest) | Creates a Skopeo manifest for a set of images. |
| [workflow-concurrency](./workflow-concurrency) | Control the concurrency of a GitHub workflow. |
