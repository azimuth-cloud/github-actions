# github-actions

This repository contains common GitHub Actions that are shared between multiple StackHPC
repositories.

## Available actions

Currently, the available actions are:

| Name | Description |
|---|---|
| [docker-multiarch-build-push](./docker-multiarch-build-push) | Build and optionally push a multi-architecture Docker image. |
| [helm-publish](./helm-publish) | Publish the Helm charts from the given directory to another branch in the repository (e.g. `gh-pages`). |
| [semver](./semver) | Generate a [SemVer](https://semver.org/) compatible version for the current commit. |
