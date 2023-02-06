# semver GitHub Action

This GitHub Action generates a [SemVer](https://semver.org/) compliant version for the current
commit using a combination of the last tag, the distance from that tag and the name of the
branch that the commit is on. The versions are constructed so that the versions for a particular
branch will order correctly.

> **WARNING**
>
> This assumes that tags are SemVer compliant of the form `{major}.{minor}.{patch}[-{prerelease}]`,
> e.g. `0.3.0`, `1.2.10`, `2.0.0-alpha.1`, `2.0.0-beta.3`, `2.0.0-rc.2`.

The generated versions are of the form:

```
{tag}[-dev.0][.{branch}.{distance}]
```

Examples:

  * For a tag, the returned version will just be the tag.
  * For a branch `feature` that is 10 commits on from the `1.1.0` tag, the version will
    be `1.1.1-dev.0.feature.10`. Note that the patch version has been incremented as
    this is considered a pre-release version of the next release.
  * For a branch `feature2` that is 5 commits on from the `1.2.0-alpha.1` tag, the version
    will be `1.2.0-alpha.1.feature2.5`. Because the tag already has a pre-release version,
    the "fake" pre-release version `dev.0` is not added and the patch version is not
    incremented.

> **WARNING**
>
> The `actions/checkout` invocation that precedes the semver action must include
> `fetch-depth: 0` in the inputs (see below for an example).
>
> Without this, the action is unable to determine the distance from the last tag
> as it only has information about the most recent commit.

See the [action.yml](./action.yml) for more information.

## Usage

The following job uses this action to publish all the Helm charts from a repository
to the `gh-pages` branch using the `version` and `app-version` from the semver action:

```yaml
build_push_chart:
  name: Build and push Helm chart
  runs-on: ubuntu-latest
  steps:
    - name: Check out the repository
      uses: actions/checkout@v3
      with:
        # This is important for the semver action to work correctly
        # when determining the number of commits since the last tag
        fetch-depth: 0

    - name: Get SemVer version for current commit
      id: semver
      uses: stackhpc/github-actions/semver@main

    # Produces something like "1.0.5-dev.0.feature.10  3c7fdeb"
    - run: echo ${{ steps.semver.outputs.version }}  ${{ steps.semver.outputs.short-sha }}
```
