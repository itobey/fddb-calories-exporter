# never use a development version as requirements for pip install are not met
FROM python:3.9.6-alpine3.13

RUN apk update && apk upgrade

RUN apk add --update curl gcc g++ postgresql-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

RUN apk add --no-cache tzdata
ENV TZ=Europe/Berlin

COPY requirements.txt /

RUN pip3 install -r /requirements.txt

COPY exporter.py /
