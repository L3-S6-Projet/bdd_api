from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()
try:
    User.objects.create_superuser('test', 'admin@test.com', 'passwdtest')
    print('Created user')
except IntegrityError:
    print('User already exists')
