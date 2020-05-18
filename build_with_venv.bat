@ECHO OFF
venv\Scripts\activate.bat && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && python manage.py shell < insert_test_data.py && venv\Scripts\deactivate.bat
