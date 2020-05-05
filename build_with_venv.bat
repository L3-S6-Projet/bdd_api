@ECHO OFF
venv\Scripts\activate.bat && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && echo import setup | python manage.py shell && venv\Scripts\deactivate.bat
