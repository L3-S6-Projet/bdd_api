from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()
try:
    User.objects.create_superuser('test', 'admin@test.com', 'passwdtest')
except IntegrityError:
    pass
