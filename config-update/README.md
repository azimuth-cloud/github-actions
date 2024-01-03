# config-update GitHub Action

This GitHub Action writes values into the specified path in a structured config file, with
as much effort as possible given to ensuring a clean diff.

Currently, this action is able to update values in:

  * JSON files
  * YAML files
  * Build arg default values in `Dockerfile`s

In all cases, the path to update is given using the JSONPath syntax supported by
[jsonpath-ng](https://github.com/h2non/jsonpath-ng).

See the [action.yml](./action.yml) for more information.

## Usage

In the following example, two keys are updated in a config file from variables:

```yaml
do_something:
  runs-on: ubuntu-latest
  steps:
    - name: Update config
      uses: stackhpc/github-actions/config-update@master
      with:
        path: repo/path/to/config.json
        updates: |
          path.to.item1=${{ env.ITEM1 }}
          path.to.item2=${{ env.ITEM2 }}
```
