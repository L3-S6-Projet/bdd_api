@ECHO OFF
venv\Scripts\activate.bat && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('test', 'admin@test.com', 'passwdtest') | python manage.py shell && venv\Scripts\deactivate.bat
