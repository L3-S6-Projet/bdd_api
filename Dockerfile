FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /scolendar

WORKDIR /scolendar

ADD . /scolendar/

RUN pip install -r requirements.txt