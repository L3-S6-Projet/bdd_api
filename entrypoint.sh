#!/bin/bash
sh docker_build.sh && python manage.py runserver 0:8000
