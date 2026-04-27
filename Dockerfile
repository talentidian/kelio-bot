FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

ENV TZ=Europe/Madrid \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    KELIO_DATA_DIR=/data

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates tzdata \
    && ln -sf /usr/share/zoneinfo/Europe/Madrid /etc/localtime \
    && echo "Europe/Madrid" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

ARG SUPERCRONIC_VERSION=v0.2.29
RUN curl -fsSLO "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
    && mv supercronic-linux-amd64 /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY holidays_check.py pto.py kelio_clock.py notify.py crontab entrypoint.sh ./
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]