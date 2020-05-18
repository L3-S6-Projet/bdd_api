#!/bin/bash
source .venv/bin/activate && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && python manage.py shell <insert_test_data.py && deactivate
