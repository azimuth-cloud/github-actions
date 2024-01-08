# k8s-extract-images GitHub Action

This GitHub Action attempts to extract the required images from a file containing Kubernetes
manifests.

The images are output as a JSON-formatted list that can be used with the
[fromJSON function](https://docs.github.com/en/actions/learn-github-actions/expressions#fromjson).

This can be combined with the [helm-template](../helm-template) action to extract the required
image from a Helm chart.

See the [action.yml](./action.yml) for more information.

## Usage

In the following example, images are extracted from the
[kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
chart:

```yaml
extract_images:
  runs-on: ubuntu-latest
  steps:
    - name: Template chart
      id: helm-template
      uses: stackhpc/github-actions/helm-template@master
      with:
        repository: https://prometheus-community.github.io/helm-charts
        chart: kube-prometheus-stack
        version: 55.5.1

    - name: Extract images
      uses: stackhpc/github-actions/k8s-extract-images@master
      with:
        manifests-file: ${{ steps.helm-template.outputs.manifests-file }}
```
