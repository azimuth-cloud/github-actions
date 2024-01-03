# docker-multiarch-build-push GitHub Action

This GitHub Action builds, scans and (optionally) pushes a multi-architecture
Docker image using [Docker buildx](https://docs.docker.com/buildx/working-with-buildx/)
and [QEMU](https://www.qemu.org/).

It also makes use of the
[GitHub Actions cache](https://docs.github.com/en/actions/advanced-guides/caching-dependencies-to-speed-up-workflows)
to preserve the Docker build cache between runs.

See the [action.yml](./action.yml) for more information.

## Usage

The following job uses this action to build and push a multi-architecture image to
[GitHub Packages](https://github.com/features/packages) with some standard tags
(short-sha and branch name for all commits; tag if ref is a tag):

```yaml
build_push_image:
  name: Build and push image
  runs-on: ubuntu-latest
  steps:
    - name: Check out the repository
      uses: actions/checkout@v3

    - name: Login to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Calculate metadata for image
      id: image-meta
      uses: docker/metadata-action@v4
      with:
        images: ghcr.io/my-org/my-image
        # Produce the branch name or tag and the SHA as tags
        tags: |
          type=ref,event=branch
          type=ref,event=tag
          type=sha,prefix=

    - name: Build and push image
      uses: stackhpc/github-actions/docker-multiarch-build-push@master
      with:
        cache-key: my-image
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.image-meta.outputs.tags }}
        labels: ${{ steps.image-meta.outputs.labels }}
```
