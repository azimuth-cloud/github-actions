# helm-publish GitHub Action

This GitHub Action publishes all the Helm charts from the given `directory` (defaults to
the entire repository) to another `branch` in the same repository (defaults to `gh-pages`).

By default, the `version` and `appVersion` from the Helm chart are used, however these can
be overridden using the `version` and `app-version` inputs. A common use case for this is
to consume the output of the [semver action](../semver) - this works very well for ensuring
consistency when the same repository builds and pushes an image before publishing the
corresponding Helm chart. In this case, the images are tagged with the short-sha, which is
used as the `appVersion` of the Helm chart and is default tag for the images, and the Helm
chart `version` is set to the SemVer version for the commit. This means that every commit
is available as a `--devel` version in the Helm repository, and each version of the Helm
chart is tied to the corresponding version of the images.

The resulting branch can be published as a
[Helm repository](https://helm.sh/docs/topics/chart_repository/) using
[GitHub Pages](https://pages.github.com/).

See the [action.yml](./action.yml) for more information.

## Usage

The following job uses this action to publish all the Helm charts from a repository
to the `gh-pages` branch using the `version` and `app-version` from the semver action:

```yaml
build_push_chart:
  name: Build and push Helm chart
  runs-on: ubuntu-latest
  steps:
    - name: Check out the repository
      uses: actions/checkout@v2
      with:
        # This is important for the semver action to work correctly
        # when determining the number of commits since the last tag
        fetch-depth: 0

    - name: Get SemVer version for current commit
      id: semver
      uses: stackhpc/github-actions/semver@main

    - name: Publish Helm charts
      uses: stackhpc/github-actions/helm-publish@main
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
        version: ${{ steps.semver.outputs.version }}
        app-version: ${{ steps.semver.outputs.short-sha }}
```
