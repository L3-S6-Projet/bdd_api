@ECHO OFF
venv\Scripts\activate.bat && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && python manage.py shell < setup.py && venv\Scripts\deactivate.bat
