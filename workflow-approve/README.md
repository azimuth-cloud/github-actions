# workflow-approve GitHub Action

This GitHub Action ensures that a workflow run has been approved before allowing
execution to continue.

This is achieved by posting a comment to the relevant PR and waiting for either
a thumbs-up or thumbs-down on the comment from one of the designated approvers.

See the [action.yml](./action.yml) for more information.

## Usage

In the following example, the `actual_work` job will only execute once approval
has been given:

```yaml
wait_for_approval:
  runs-on: ubuntu-latest
  steps:
    - name: Wait for approval
      uses: azimuth-cloud/github-actions/workflow-approve@master
      with:
        # Comma-separated list of users who can approve the workflow
        approvers: user1,user2

actual_work:
  needs: [wait_for_approval]
  # ... job definition ...
```

The action also supports designating workflows as "automatically approved". This
is designed for use with `pull_request_target`, where the workflow that runs is
the one from the target branch (usually `main`). For instance, in the following
workflow, runs from the same repo as the target branch are automatically approved
while workflow runs from other repositories require explicit approval:

```yaml
wait_for_approval:
  runs-on: ubuntu-latest
  steps:
    - name: Wait for approval
      uses: azimuth-cloud/github-actions/workflow-approve@master
      with:
        approvers: user1,user2
        approval-required: ${{ github.event.pull_request.head.repo.full_name != github.repository }}

actual_work:
  needs: [wait_for_approval]
  # ... job definition ...
```
