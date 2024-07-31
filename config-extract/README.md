# config-extract GitHub Action

This GitHub Action extracts values from config files and makes them available as outputs.

Currently, this action is able to extract values from:

  * JSON files
  * YAML files
  * Build arg default values in `Dockerfile`s

See the [action.yml](./action.yml) for more information.

## Usage

In the following example, two keys are extracted from a config file then used in the next step:

```yaml
do_something:
  runs-on: ubuntu-latest
  steps:
    - name: Extract config items
      id: config
      uses: azimuth-cloud/github-actions/config-extract@master
      with:
        outputs: |
          item1=path.to.item.one
          item2=path.to.item.two

    - name: Echo config items
      run: echo ${{ steps.config.outputs.item1 }} ${{ steps.config.outputs.item2 }}
```
