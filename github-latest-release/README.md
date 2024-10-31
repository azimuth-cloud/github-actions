# github-latest-release GitHub Action

This GitHub Action outputs the latest GitHub release for a repository.

See the [action.yml](./action.yml) for more information.

## Usage

The following gets the latest release of Helm and echoes it:

```yaml
helm_latest:
  runs-on: ubuntu-latest
  steps:
    - name: Get latest release for helm/helm
      id: helm
      uses: azimuth-cloud/github-actions/github-latest-release@master
      with:
        repository: helm/helm

    - name: Echo version
      run: echo ${{ steps.helm.outputs.version }}
```
