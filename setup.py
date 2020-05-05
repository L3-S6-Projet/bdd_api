from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from scolendar.models import Student, Class, Teacher

User = get_user_model()
try:
    User.objects.create_superuser('super', 'super@test.com', 'passwdtest')
except IntegrityError:
    pass

try:
    user = User.objects.create_user('admin', 'admin@test.com', 'passwdtest')
    user.is_staff = True
    user.save()
except IntegrityError:
    pass

try:
    _class = Class(name='L3 Informatique', level='L3')
    _class.save()
except IntegrityError:
    _class = Class.objects.get(name='L3 Informatique', level='L3')

try:
    student = Student(username='stu1', _class=_class)
    student.set_password('passwdtest')
    student.save()
except IntegrityError:
    pass

try:
    teacher = Teacher(username='tea1', email='teacher@test.com', phone_number='06 61 66 16 61')
    teacher.set_password('passwdtest')
    teacher.save()
except IntegrityError:
    pass
