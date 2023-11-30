# workflow-concurrency GitHub Action

This GitHub Action ensures that only a maximum number of workflow runs are able to
concurrently pass the point in the workflow where this action runs.

The size of the queue is limited to three runs by default to save on busy waiting time.
This can be configured using the `queue-size` parameter. Alternatively, this can be set
to a large size and controlled using a
[job timeout](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idtimeout-minutes).
on the job that does the waiting.

Existing workflow runs for the same workflow and branch can optionally be cancelled.
This is configured using `cancel-existing`, which defaults to `no`.

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
