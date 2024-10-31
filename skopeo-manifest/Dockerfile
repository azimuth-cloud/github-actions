FROM python:3.9

ENV PYTHONUNBUFFERED 1

RUN pip install --no-cache-dir pyyaml

COPY skopeo-manifest.py /usr/local/bin/skopeo-manifest

ENTRYPOINT ["skopeo-manifest"]
