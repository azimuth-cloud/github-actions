FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Install the requirements
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir requests

COPY workflow-approve.py /usr/local/bin/workflow-approve

ENTRYPOINT ["workflow-approve"]
