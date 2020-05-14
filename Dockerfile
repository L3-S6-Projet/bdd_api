FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /scolendar

WORKDIR /scolendar

COPY . /scolendar/

RUN pip install -r requirements.txt

RUN chmod +x docker_build.sh

RUN sh docker_build.sh

EXPOSE 8000

CMD [ "python", "manage.py", "runserver", "0:8000" ]