FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Add the GitHub workspace to the list of trusted directories
RUN git config --system --add safe.directory /github/workspace

COPY semver.py /usr/local/bin/semver

ENTRYPOINT ["semver"]
