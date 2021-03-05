# never use a development version as requirements for pip install are not met
FROM python:3.9.2-buster

RUN apt-get update && \
	apt-get upgrade -y 

COPY requirements.txt /

RUN pip3 install -r /requirements.txt

COPY exporter.py /
