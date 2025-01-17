# generate-app-token GitHub Action

This GitHub Actions generates an
[installation access token](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)
for a [GitHub App](https://docs.github.com/en/apps/overview) that is installed for a repository.
Using this token, an action can authenticate as the app and perform actions that are not permitted
for the default `GITHUB_TOKEN`, such as creating PRs that trigger additional workflows.

See the [action.yml](./action.yml) for more information.

## Creating an app

Before you can use this action, you must first
[create an app](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app)
that will be used to issue tokens. The homepage URL can be set to anything. You should uncheck
`Active` under `Webhook`, and there is no need to enter a webhook URL.

Keep a record of the app ID for later.

The app should be given whatever permissions are required to perform the action that the token
is being used for. For instance, if you are using the token to create PRs, it will need the
following permissions:

  * `Repository permissions > Contents > Access: Read & write`
  * `Repository permissions > Pull requests > Access: Read & write`

If you want to add teams as reviewers on PRs, you will also need to add:

  * `Organization permissions > Members > Access: Read-only`

You will then need to
[install the app](https://docs.github.com/en/apps/using-github-apps/installing-your-own-github-app)
on any repositories that need to make tokens.

The final step is to
[generate a private key](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/managing-private-keys-for-github-apps)
for the app and save it somewhere safe.

The app ID and private key will need to be set as secrets on any repositories that need to
generate tokens using the app.

## Usage

The following job uses this action to create a token that is used to create a PR that
triggers additional workflows:

```yaml
build_push_chart:
  name: Build and push Helm chart
  runs-on: ubuntu-latest
  steps:
    - name: Check out the repository
      uses: actions/checkout@v4

    - name: Generate app token for PR
      uses: azimuth-cloud/github-actions/generate-app-token@master
      id: generate-app-token
      with:
        repository: ${{ github.repository }}
        app-id: ${{ secrets.APP_ID }}
        app-private-key: ${{ secrets.APP_PRIVATE_KEY }}

    - name: Propose changes via PR if required
      uses: peter-evans/create-pull-request@v7
      with:
        token: ${{ steps.generate-app-token.outputs.token }}
        commit-message: Some automated changes
        branch: update/automation
        delete-branch: true
        title: Proposing some automated changes
        labels: |
          automation
```
