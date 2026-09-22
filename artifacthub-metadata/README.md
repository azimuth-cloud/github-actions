# artifacthub-metadata GitHub Action

This GitHub Action publishes `artifacthub-repo.yaml` metadata file to the same GHCR
repository as the Helm chart it is co-located with.

The metadata file lives in the chart directory but is not used by Helm, instead it is
pushed to the same OCI repository with the special tag `artifacthub.io` and gets read
by artifacthub when it scans the repository.

See the [action.yml](./action.yml) for more information.

## Usage

The following job uses this action to publish the metadata for `my-chart`:

```yaml
push_artifact_metadata:
  name: Push artifacthub metadata
  runs-on: ubuntu-latest
  steps:
    - name: Check out the repository
      uses: actions/checkout@v4
      with:
        # This is important for the semver action to work correctly
        # when determining the number of commits since the last tag
        fetch-depth: 0

    - name: Push metadata
      uses: azimuth-cloud/github-actions/artifacthub-metadata@master
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
        directory: ./my-chart
```
