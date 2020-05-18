#!/bin/bash
python manage.py makemigrations && python manage.py migrate && echo "import insert_test_data" | python manage.py shell
