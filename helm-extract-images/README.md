# helm-extract-images GitHub Action

This GitHub Action attempts to extract the required images from a Helm chart.

## Images in chart values

The action will search the chart default values for objects of the form:

```yaml
repository: quay.io/prometheus/prometheus
tag: v2.48.1
```

An optional `registry` field is also supported, and is prepended to the image if found.

If the tag field is present but empty, the chart `appVersion` is used as the tag.

## Images in templated manifests

The action will also template the manifests using the given values, search for any workloads
in the rendered manifests and return the images used by those as well.

## Usage

In the following example, images are extracted from the
[kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
chart:

```yaml
extract_images:
  runs-on: ubuntu-latest
  steps:
    - name: Extract images
      uses: stackhpc/github-actions/helm-extract-images@master
      with:
        repository: https://prometheus-community.github.io/helm-charts
        chart: kube-prometheus-stack
        version: 55.5.1
        values: |
          grafana:
            enabled: true
```

See the [action.yml](./action.yml) for more information.
