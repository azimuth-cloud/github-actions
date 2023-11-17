FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Install the requirements
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir easysemver requests

COPY github-latest-release.py /usr/local/bin/github-latest-release

ENTRYPOINT ["github-latest-release"]
