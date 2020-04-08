from datetime import date, time, timedelta, datetime

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from conf import conf


def start_time_validator(time_to_validate: time):
    if conf.start_time() > time_to_validate:
        raise ValidationError(_('L\'heure de début n\'est pas valide'))


def end_time_validator(event_date: date, start_time: time, duration: timedelta):
    if datetime.combine(event_date, conf.end_time()) < datetime.combine(event_date, start_time) + duration:
        raise ValidationError(_('L\'heure de fin n\'est pas valide'))
