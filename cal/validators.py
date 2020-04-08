from datetime import time

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from conf import conf


def start_time_validator(time_to_validate: time):
    start_time = conf.start_time()
    if conf.start_time() > time_to_validate:
        raise ValidationError(_(f'L\'établissement n\'ouvre pas avant {start_time.strftime("%H:%M")}'))
