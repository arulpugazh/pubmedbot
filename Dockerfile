FROM ubuntu:18.04
LABEL maintainer="arulpugazh"
LABEL repository="pubmedbot"

ENV TZ=America/Toronto
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && \
    apt install -y bash \
    git \
    python3 \
    python3-pip \
    libpq-dev

RUN rm -rf /var/lib/apt/lists

RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --log pip_log.txt --no-cache-dir \
    farm-haystack\
    dash \
    dash-bootstrap-components \
    google-api-python-client \
    google-auth \
    google-cloud-storage \
    psycopg2


COPY app.py .
COPY gcputils.py .
COPY dbutils.py .
COPY google_credentials.json .
EXPOSE 80
CMD ["python3", "app.py"]