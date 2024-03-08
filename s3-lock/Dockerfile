FROM python:3.9

ENV PYTHONUNBUFFERED 1

# Install the requirements
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir boto3

COPY s3-lock.py /usr/local/bin/s3-lock

ENTRYPOINT ["s3-lock"]
