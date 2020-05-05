FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /scolendar_api

WORKDIR /scolendar_api

ADD . /scolendar_api/

RUN pip install -r requirements.txt

COPY build_without_venv.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]