#!/usr/bin/env python3

import os
import time

import jwt
import requests


#####
# This script generates an app token for a repository
#
# https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation
#####


def get_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set or empty")
    return value

repository = get_env("REPOSITORY")
app_id = get_env("APP_ID")
app_private_key = get_env("APP_PRIVATE_KEY")


# First, we need to make a JWT for the app
iat = int(time.time())
payload = { "iat": iat, "exp": iat + 600, "iss": app_id }
encoded_jwt = jwt.encode(payload, app_private_key, algorithm = "RS256")

# Use the JWT to get the access token URL for the repo installation
response = requests.get(
    f"https://api.github.com/repos/{repository}/installation",
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {encoded_jwt}",
    }
)
response.raise_for_status()
access_token_url = response.json()["access_tokens_url"]

# Use the installation ID to get an access token for the repo
response = requests.post(
    access_token_url,
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {encoded_jwt}",
    },
    json = {
        "repositories": [
            # Because the installation is associated with an org or user,
            # we only need to specify the name part of the repo here
            repository.split("/", maxsplit = 1)[-1],
        ],
    }
)
response.raise_for_status()
token = response.json()["token"]

# Output the token so it can be consumed by later steps
output_path = os.environ.get("GITHUB_OUTPUT", "/dev/stdout")
with open(output_path, "a") as fh:
    print(f"token={token}", file = fh)
