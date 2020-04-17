from datetime import time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from conf import conf
from users.models import UserInfo


def start_time_validator(time_to_validate: time):
    start_time = conf.start_time()
    if conf.start_time() > time_to_validate:
        raise ValidationError(_(f'L\'établissement n\'ouvre pas avant {start_time.strftime("%H:%M")}'))


def max_duration_validation(duration_to_validate: timedelta):
    seconds = conf.max_duration().seconds
    h = seconds // 3600
    m = (seconds // 60) % 60
    hour = str(h) if len(str(h)) == 2 else f'0{h}'
    minute = str(m) if len(str(m)) == 2 else f'0{m}'
    if conf.max_duration() < duration_to_validate:
        raise ValidationError(_(f'La durée d\'une séance ne peut dépasser {hour}:{minute}'))


def teacher_validator(person):
    if UserInfo.objects.filter(user=User.objects.filter(id=person)[0])[0].type != 'INT':
        raise ValidationError(_('Veuillez choisir un intervenant et pas un élève'))


def student_validator(person):
    if person is None:
        return
    if UserInfo.objects.filter(user=User.objects.filter(id=person)[0])[0].type != 'STU':
        raise ValidationError(_('Veuillez choisir un élève et pas un intervenant'))
