#!/bin/bash
sh docker_build.sh && python manage.py runserver 0:3030
