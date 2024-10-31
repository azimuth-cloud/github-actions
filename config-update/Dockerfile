FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Install the requirements
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir jsonpath-ng ruamel.yaml

COPY config-update.py /usr/local/bin/config-update

ENTRYPOINT ["config-update"]
