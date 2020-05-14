#!/bin/bash
python manage.py makemigrations && python manage.py migrate && echo "import setup" | python manage.py shell