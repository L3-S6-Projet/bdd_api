FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /scolendar_api

WORKDIR /scolendar_api

ADD . /scolendar_api/

RUN pip install -r requirements.txt

COPY entrypoint.sh /build_without_venv.sh

ENTRYPOINT ["/entrypoint.sh"]