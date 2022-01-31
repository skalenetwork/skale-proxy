FROM python:3.8-buster

RUN apt-get update

RUN mkdir /usr/src/proxy /data
WORKDIR /usr/src/proxy

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH="/usr/src/proxy"
ENV COLUMNS=80

CMD python /usr/src/proxy/proxy/main.py
