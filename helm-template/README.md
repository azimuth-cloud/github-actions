# helm-template GitHub Action

This GitHub Action templates a chart using `helm template` and outputs the resulting manifests
to a file.

The file into which manifests are written is available as the `manifests-file` output. It can
be customised using the `manifests-file` parameter, which defaults to `manifests.yaml`.

See the [action.yml](./action.yml) for more information.

## Usage

In the following example, the
[kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
chart is templated to produce manifests:

```yaml
template_manifests:
  runs-on: ubuntu-latest
  steps:
    - name: Template manifests
      uses: azimuth-cloud/github-actions/helm-template@master
      with:
        repository: https://prometheus-community.github.io/helm-charts
        chart: kube-prometheus-stack
        version: 55.5.1
        values: |
          grafana:
            enabled: true
```
