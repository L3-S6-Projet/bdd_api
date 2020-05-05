import re
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from conf import conf


def class_name_validator(name: str):
    from .models import level_list
    if not name.startswith(tuple([i[0] for i in level_list])):
        raise ValidationError(_('Nom de classe incorrect'))


def start_datetime_validator(datetime_to_validate: datetime):
    start_time = conf.start_time()
    if conf.start_time() > datetime_to_validate.time():
        raise ValidationError(_(f'L\'établissement n\'ouvre pas avant {start_time.strftime("%H:%M")}'))


def max_duration_validator(duration_to_validate: timedelta):
    seconds = conf.max_duration().seconds
    h = seconds // 3600
    m = (seconds // 60) % 60
    hour = str(h) if len(str(h)) == 2 else f'0{h}'
    minute = str(m) if len(str(m)) == 2 else f'0{m}'
    if conf.max_duration() < duration_to_validate:
        raise ValidationError(_(f'La durée d\'une séance ne peut dépasser {hour}:{minute}'))


def phone_number_validator(to_check: str):
    pattern = re.compile(r'^(\+\d{1,3}\D?)?(\d{2}|\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$', re.VERBOSE)
    if not pattern.search(to_check):
        raise ValidationError(_('Le format du numéro n\'est pas correct'))
