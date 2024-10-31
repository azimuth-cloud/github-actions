# s3-lock GitHub Action

This GitHub Action attempts to use S3 to implement a rudimentary lock. This is primarily
to allow GitHub Actions in multiple projects to coordinate access to a limited resource.

> **NOTE**
> 
> This is a "best effort" lock - it cannot *guarantee* that only one workflow run
> can acquire the lock because S3 lacks the primitives to implement this.
>
> However it should be good enough for most cases.

It implements two actions - `acquire` and `release` - that are used to acquire and
release the lock respectively.

Both actions require S3 credentials and the location of the lock to be specified
using the following parameters:

  * `host` - the S3 host (without scheme)
  * `access-key` - the S3 access key
  * `secret-key` - the S3 secret key
  * `bucket` - the name of the bucket to use (must already exist)
  * `lock-file` - the name of the lock object (defaults to `.lockfile`)

By using the same lock location in multiple projects, you get a cross-project lock.

The `acquire` action supports a `wait` parameter that will make the workflow run
busy wait until the lock can be acquired. This defaults to `true`.

The `release` action should be run after the workflow run is complete, and must be
run whether it succeeds, fails or is cancelled (i.e. using `if: ${{ always() }}`).

There is a fail-safe against a workflow run failing to release the lock in the form
of the `deadlock-timeout` parameter. If a workflow run fails to release the lock
after the specified number of seconds, then the lock is acquired by the next workflow
run regardless. The `deadlock-timeout` should be set to longer than the longest
execution time for a well-behaved workflow. The default is `10800`, i.e. 3 hours.

See the [action.yml](./action.yml) for more information.

## Usage

In the following example, the lock is acquired and then released.

```yaml
do_something:
  runs-on: ubuntu-latest
  steps:
    # Waits until the lock can be acquired
    - name: Acquire lock
      uses: azimuth-cloud/github-actions/s3-lock@master
      with:
        host: ${{ vars.S3_HOST }}
        access-key: ${{ secrets.S3_ACCESS_KEY }}
        secret-key: ${{ secrets.S3_SECRET_KEY }}
        bucket: lock-bucket
        action: acquire

    # Do some stuff

    - name: Release lock
      uses: azimuth-cloud/github-actions/s3-lock@master
      if: ${{ always() }}
      with:
        host: ${{ vars.S3_HOST }}
        access-key: ${{ secrets.S3_ACCESS_KEY }}
        secret-key: ${{ secrets.S3_SECRET_KEY }}
        bucket: lock-bucket
        action: release
```
