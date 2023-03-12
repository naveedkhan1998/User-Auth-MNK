FROM python:3.10-alpine

ENV PYTHONNUMBUFFERED 1
RUN apk update
RUN apk add make
RUN apk add musl-dev wget git build-base linux-headers g++ gcc libffi-dev openssl-dev cargo
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev


#mysql client
RUN apk add --no-cache mariadb-connector-c-dev
RUN apk add mariadb-connector-c
RUN apk update && apk add mariadb-dev && pip3 install mysqlclient && apk del mariadb-dev

RUN mkdir /app
WORKDIR /app
RUN pip3 install --upgrade pip setuptools
RUN pip3 install psycopg2-binary
RUN pip3 install gunicorn
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
RUN apk add --no-cache libstdc++
RUN pip3 install pyopenssl --upgrade
RUN apk del musl-dev wget git build-base linux-headers g++ gcc libffi-dev openssl-dev cargo
COPY . /app

EXPOSE 8000
RUN chmod +x /app/start.sh
ENTRYPOINT ["./start.sh"]