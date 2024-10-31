# helm-latest-version GitHub Action

This GitHub Action outputs the latest version for a Helm chart, with optional constraints.

See the [action.yml](./action.yml) for more information.

## Usage

The following gets the latest version of the cert-manager chart and echoes it:

```yaml
cert_manager_latest:
  runs-on: ubuntu-latest
  steps:
    - name: Get latest version for cert-manager
      id: cert-manager
      uses: azimuth-cloud/github-actions/helm-latest-version@master
      with:
        repository: https://charts.jetstack.io
        chart: cert-manager
        # Constraints are optional
        # By default, all stable versions are considered
        constraints: "<1.13.0"

    - name: Echo version
      run: echo ${{ steps.cert-manager.outputs.version }}
```
