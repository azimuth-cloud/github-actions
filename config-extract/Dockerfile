FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Install the requirements
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir jsonpath-ng pyyaml

COPY config-extract.py /usr/local/bin/config-extract

ENTRYPOINT ["config-extract"]
