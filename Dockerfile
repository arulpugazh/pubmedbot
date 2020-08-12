FROM nvidia/cuda:11.0-runtime-ubuntu20.04
LABEL maintainer="arulpugazh"
LABEL repository="pubmedbot"

RUN apt update && \
    apt install -y bash \
                   build-essential \
                   git \
                   curl \
                   ca-certificates \
                   python3 \
                   python3-pip \
                   libpq-dev

RUN rm -rf /var/lib/apt/lists

RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir \
    farm-haystack\
    mkl \
    dash \
    beautifulsoup4 \
    requests \
    retrying \
    pysocks \
    pandas \
    pymupdf \
    google-api-python-client \
    sqlalchemy \
    psycopg2 \
    google-auth \
    google-api-python-client \
    gsutil

RUN git clone https://github.com/arulpugazh/pubmedbot.git
COPY google_credentials.json pubmedbot/
RUN cd pubmedbot
ENV GOOGLE_APPLICATION_CREDENTIALS=pubmedbot/google_credentials.json
RUN gsutil cp gs://pubmedbot/10k_articles.csv pubmedbot/
EXPOSE 5000/tcp
RUN /bin/bash -c "ls pubmedbot/"
CMD ["python3", "pubmedbot/app.py"]
