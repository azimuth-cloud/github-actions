#!/usr/bin/env python3

"""
This script implements a rudimentary lock in S3.
"""

import argparse
import json
import os
import sys
import time

import boto3


class S3Bucket:
    def __init__(self, host, access_key, secret_key, bucket):
        self.s3 = boto3.client(
            "s3",
            endpoint_url = f"https://{host}",
            aws_access_key_id = access_key,
            aws_secret_access_key = secret_key
        )
        self.bucket = bucket

    def fetch_key(self, key):
        """
        Fetches the data for a key.
        """
        try:
            return self.s3.get_object(Bucket = self.bucket, Key = key)["Body"].read()
        except self.s3.exceptions.NoSuchKey:
            return None

    def put_key(self, key, content):
        """
        Puts the given content at the given key.
        """
        self.s3.put_object(Bucket = self.bucket, Key = key, Body = content)

    def delete_key(self, key):
        """
        Deletes a key in the bucket.
        """
        self.s3.delete_object(Bucket = self.bucket, Key = key)


class S3Lock:
    def __init__(self, bucket, lock_file, process_id):
        self.bucket = bucket
        self.lock_file = lock_file
        self.process_id = process_id

    def _can_acquire_lock(self, deadlock_timeout):
        content = self.bucket.fetch_key(self.lock_file)
        # If there is no lock file, we can acquire it
        if not content:
            return True, None
        lock = json.loads(content)
        # If we own the lock, we can re-acquire it with a newer timestamp
        if lock["process_id"] == self.process_id:
            return True, None
        # If the timestamp is older than the deadlock timeout, we can acquire it
        if lock["timestamp"] + deadlock_timeout < time.time():
            return True, None
        # If another process owns the lock, we cannot acquire it
        return False, lock["process_id"]

    def _put_lock_content(self):
        lock = {"process_id": self.process_id, "timestamp": time.time()}
        self.bucket.put_key(self.lock_file, json.dumps(lock).encode())

    def _check_lock_acquired(self):
        content = self.bucket.fetch_key(self.lock_file)
        if content:
            lock = json.loads(content)
            return lock["process_id"] == self.process_id
        else:
            return False

    def acquire(self, wait, deadlock_timeout, poll_interval):
        """
        Acquire the lock.
        """
        while True:
            can_acquire, current_holder = self._can_acquire_lock(deadlock_timeout)
            if can_acquire:
                self._put_lock_content()
                # Wait long enough that any processes that saw the lock content
                # before we did our put have also put their lock content
                time.sleep(2)
                # See if we won the race to put our lock content
                if self._check_lock_acquired():
                    return True
            else:
                print(f"[WARN ]   failed to acquire lock - currently held by '{current_holder}'")
            if wait:
                time.sleep(poll_interval)
            else:
                return False

    def release(self):
        """
        Release the lock.
        """
        # Only release the lock if we own it
        if self._check_lock_acquired():
            self.bucket.delete_key(self.lock_file)
            return True
        else:
            print("[WARN ] lock not owned by current process")
            return False


def add_argument_with_envvar(parser, *args, **kwargs):
    """
    Adds an argument that can be set using an envvar.
    """
    envvar = kwargs.pop("envvar")
    envvar_value = os.environ.get(envvar) or None
    kwargs.setdefault("default", envvar_value)
    kwargs.setdefault("required", envvar_value is None)
    parser.add_argument(*args, **kwargs)


def main():
    parser = argparse.ArgumentParser(description = "Implements a rudimentary lock in S3.")
    add_argument_with_envvar(
        parser,
        "--host",
        envvar = "S3_HOST",
        help = "The S3 host to use."
    )
    add_argument_with_envvar(
        parser,
        "--access-key",
        envvar = "S3_ACCESS_KEY",
        help = "The S3 access key to use."
    )
    add_argument_with_envvar(
        parser,
        "--secret-key",
        envvar = "S3_SECRET_KEY",
        help = "The S3 secret key to use."
    )
    add_argument_with_envvar(
        parser,
        "--bucket",
        envvar = "S3_BUCKET",
        help = "The S3 bucket to use (must already exist)."
    )
    parser.add_argument(
        "--lock-file",
        default = ".lockfile",
        help = "The name of the lock file."
    )
    parser.add_argument(
        "--wait",
        action = argparse.BooleanOptionalAction,
        default = True,
        help = "Whether to busy-wait until the lock is acquired.",
    )
    parser.add_argument(
        "--poll-interval",
        type = int,
        default = 300,
        help = "The poll interval before checking for the lock again."
    )
    parser.add_argument(
        "--deadlock-timeout",
        type = int,
        default = 10800,
        help = "The number of seconds to wait until acquiring the lock anyway."
    )
    parser.add_argument(
        "action",
        choices = ["acquire", "release"],
        help = "The action to perform."
    )
    parser.add_argument(
        "process_id",
        help = "The ID of the current process."
    )
    args = parser.parse_args()

    print(f"[INFO ] host: '{args.host}', bucket: '{args.bucket}', lock file: '{args.lock_file}', process ID: '{args.process_id}'")
    bucket = S3Bucket(args.host, args.access_key, args.secret_key, args.bucket)
    lock = S3Lock(bucket, args.lock_file, args.process_id)
    if args.action == "acquire":
        print("[INFO ] attempting to acquire lock")
        if lock.acquire(args.wait, args.deadlock_timeout, args.poll_interval):
            print("[INFO ]   lock acquired")
        else:
            print("[ERROR]   failed to acquire lock")
            sys.exit(1)
    else:
        if lock.release():
            print("[INFO ] lock released")


if __name__ == "__main__":
    main()
