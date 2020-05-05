#!/bin/bash
source .venv/bin/activate && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && echo "import setup" | python manage.py shell && deactivate