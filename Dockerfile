FROM python:3.7

ENV PYTHONUNBUFFERED 1
ENV IN_DOCKER "1"
ENV DB_HOST "db"
ENV DB_NAME "scolendar"
ENV DB_USER "scolendar"
ENV DB_PASSWORD "passwdtest"

RUN mkdir /scolendar

WORKDIR /scolendar

COPY . /scolendar/

RUN pip install -r requirements.txt

RUN chmod +x docker_build.sh
RUN chmod +x entrypoint.sh

EXPOSE 3030

CMD ["sh", "entrypoint.sh"]