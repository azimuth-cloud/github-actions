# helm-publish GitHub Action

This GitHub Action publishes the Helm chart from the given `directory` to GHCR as an OCI
artifact,

By default, the `version` and `appVersion` from the Helm chart are used, however these can
be overridden using the `version` and `app-version` inputs. A common use case for this is
to consume the output of the [semver action](../semver) - this works very well for ensuring
consistency when the same repository builds and pushes an image before publishing the
corresponding Helm chart. In this case, the images are tagged with the short-sha, which is
used as the `appVersion` of the Helm chart and is default tag for the images, and the Helm
chart `version` is set to the SemVer version for the commit. This means that every commit
is available as a `--devel` version in the Helm repository, and each version of the Helm
chart is tied to the corresponding version of the images.

By default the chart is pushed to an artifact named as `<repository-name>/<chart-name>`
where `<repository-name>` is derived from GitHub. It can be overridden with the
`repository` input. The default GitHub value for `github.repository` always includes the
GitHub organisation name so the final artifact is named like:
`ghcr.io/azimuth-cloud/<repository-name>/<chart-name>:<chart-version>`.

The resulting artifact can be used via `helm pull`.

See the [action.yml](./action.yml) for more information.

## Usage

The following job uses this action to publish the Helm chart located at `my-chart` to GHCR
using the `version` and `app-version` from the semver action:

```yaml
build_push_chart:
  name: Build and push Helm chart
  runs-on: ubuntu-latest
  steps:
    - name: Check out the repository
      uses: actions/checkout@v4
      with:
        # This is important for the semver action to work correctly
        # when determining the number of commits since the last tag
        fetch-depth: 0

    - name: Get SemVer version for current commit
      id: semver
      uses: azimuth-cloud/github-actions/semver@master

    - name: Publish Helm charts
      uses: azimuth-cloud/github-actions/helm-publish@master
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
        version: ${{ steps.semver.outputs.version }}
        app-version: ${{ steps.semver.outputs.short-sha }}
        directory: ./my-chart
```
