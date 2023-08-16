FROM python:3.9

# Install the requirements
RUN pip install --no-cache-dir pyjwt requests

COPY generate-app-token.py /usr/local/bin/generate-app-token

ENTRYPOINT ["generate-app-token"]
