FROM python:3.9

RUN git config --global --add safe.directory /github/workspace

COPY semver.py /usr/local/bin/semver

ENTRYPOINT ["semver"]
