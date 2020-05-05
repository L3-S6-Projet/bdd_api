FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /scolendar_api

WORKDIR /scolendar_api

ADD . /scolendar_api/

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt