FROM python:3.10-alpine as builder

RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    make \
    linux-headers \
    g++ \
    git \
    cargo \
    wget \
    mariadb-connector-c-dev \
    mariadb-connector-c \
    mariadb-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip wheel --no-cache-dir --wheel-dir=/app/wheels -r requirements.txt

FROM python:3.10-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

COPY --from=builder /app/wheels /wheels

RUN apk add --no-cache \
    libstdc++ \
    mariadb-connector-c-dev \
    mariadb-connector-c \
    && pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir --no-index --find-links=/wheels -r /app/requirements.txt \
    && rm -rf /root/.cache

COPY . .

EXPOSE 8000

ENTRYPOINT ["./start.sh"]
