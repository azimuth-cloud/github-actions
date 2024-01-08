FROM python:3.9

ENV PYTHONUNBUFFERED 1

RUN pip install --no-cache-dir pyyaml requests

COPY k8s-extract-images.py /usr/local/bin/k8s-extract-images

ENTRYPOINT ["k8s-extract-images"]
