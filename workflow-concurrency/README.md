# workflow-concurrency GitHub Action

This GitHub Action ensures that only a maximum number of workflow runs are able to
concurrently pass the point in the workflow where this action runs.

Existing workflow runs for the same workflow and branch can optionally be cancelled
(defaults to `yes`).

See the [action.yml](./action.yml) for more information.

## Usage

In the following example, the `actual_work` job will only execute for a maximum of
two concurrent workflow runs:

```yaml
wait_in_queue:
  runs-on: ubuntu-latest
  steps:
    - name: Wait for an available slot
      uses: stackhpc/github-actions/workflow-concurrency@master
      with:
        max-concurrency: 2
        # Indicates whether to cancel existing workflow runs for the same workflow/branch
        cancel-existing: "yes|no"

actual_work:
  needs: [wait_in_queue]
  # ... job definition ...
```
