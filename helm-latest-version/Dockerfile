FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Install the requirements
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir easysemver pyyaml requests

COPY helm-latest-version.py /usr/local/bin/helm-latest-version

ENTRYPOINT ["helm-latest-version"]
