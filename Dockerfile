FROM ubuntu
LABEL maintainer="arulpugazh"
LABEL repository="pubmedbot"

RUN apt update && \
    apt install -y bash \
    git \
                   python3 \
                   python3-pip

RUN rm -rf /var/lib/apt/lists

RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir \
    farm-haystack\
    dash \
    google-api-python-client \
    google-auth

COPY app.py .
COPY gcputils.py .
COPY google_credentials.json .
EXPOSE 5000
CMD ["python3", "app.py"]
