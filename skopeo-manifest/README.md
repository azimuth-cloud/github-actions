# skopeo-manifest GitHub Action

This GitHub Action writes a manifest for use with the
[Skopeo](https://github.com/containers/skopeo)
[sync command](https://github.com/containers/skopeo/blob/main/docs/skopeo-sync.1.md)
to synchronise a set of images between registries.

The images can be given as either a JSON-formatted list or a newline-delimited list.

See the [action.yml](./action.yml) for more information.

## Usage

In the following example, images are extracted from the
[kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
chart and written to a manifest using actions from this repository:

```yaml
extract_images:
  runs-on: ubuntu-latest
  steps:
    - name: Template chart
      id: helm-template
      uses: azimuth-cloud/github-actions/helm-template@master
      with:
        repository: https://prometheus-community.github.io/helm-charts
        chart: kube-prometheus-stack
        version: 55.5.1

    - name: Extract images
      id: extract-images
      uses: azimuth-cloud/github-actions/k8s-extract-images@master
      with:
        manifests-file: ${{ steps.helm-template.outputs.manifests-file }}

    - name: Write Skopeo manifest
      uses: azimuth-cloud/github-actions/skopeo-manifest@master
      with:
        manifest-file: ./skopeo-manifests/kube-prometheus-stack.yaml
        images: ${{ steps.extract-images.outputs.images }}
```
