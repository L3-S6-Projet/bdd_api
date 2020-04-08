import datetime as dt
from datetime import date, timedelta, datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Model, CharField, IntegerField, ForeignKey, DateField, TimeField, DurationField, CASCADE
from django.utils.translation import gettext as _

from conf import conf
from .validators import start_time_validator

year = [
    ('L1', _('L1')),
    ('L2', _('L2')),
    ('L3', _('L3')),
    ('M1', _('M1')),
    ('M2', _('M2')),
]

grades = [
    ('MACO', _('Maître de conférences')),
    ('PROF', _('Professeur')),
    ('PRAG', _('PRAG')),
    ('PAST', _('PAST')),
    ('ATER', _('ATER')),
    ('MONI', _('Moniteur')),
]

session_type = [
    ('CM', _('CM')),
    ('TD', _('TD')),
    ('TP', _('TP')),
]


class Teacher(User):
    grade = CharField(max_length=4, verbose_name=_('Grade'), choices=grades, null=False)

    class Meta:
        verbose_name = _('Interevenant')
        verbose_name_plural = _('Intervenants')


class Class(Model):
    name = CharField(max_length=255, verbose_name=_('Nom'), null=False)
    year = CharField(max_length=2, verbose_name=_('Année'), choices=year, null=False)

    def save(self, *args, **kwargs):
        super(Class, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    class Meta:
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')
        unique_together = [('name', 'year',), ]


class Student(User):
    _class = ForeignKey(Class, on_delete=CASCADE, verbose_name=_('Classe'), null=False)

    class Meta:
        verbose_name = _('Étudiants')
        verbose_name_plural = _('Étudiants')


class Rooms(Model):
    name = CharField(max_length=255, verbose_name=_('Nom'), unique=True, null=False)
    capacity = IntegerField(verbose_name=_('Capacité'))

    def save(self, *args, **kwargs):
        super(Rooms, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    class Meta:
        verbose_name = _('Salle')
        verbose_name_plural = _('Salles')


class Subject(Model):
    name = CharField(max_length=255, verbose_name=_('Matière'), null=False)

    def save(self, *args, **kwargs):
        super(Subject, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    class Meta:
        verbose_name = _('Matière')
        verbose_name_plural = _('Matières')


class Occupancy(Model):
    room = ForeignKey(Rooms, on_delete=CASCADE, verbose_name=_('Salle'), null=False)
    date = DateField(verbose_name=_('Date'), null=False, default=dt.date.today)
    start_time = TimeField(verbose_name=_('Début'), null=False, validators=[start_time_validator, ], default='08:00:00')
    duration = DurationField(verbose_name=_('Durée'), null=False, default='01:00:00')
    subject = ForeignKey(Subject, on_delete=CASCADE, verbose_name=_('Matière'), null=False)
    session_type = CharField(max_length=2, verbose_name=_('Type'), null=False, choices=session_type)

    def __validate_fields(self):
        if datetime.combine(self.date, conf.end_time()) < datetime.combine(self.date, self.start_time) + self.duration:
            raise ValidationError(_(f'L\'établissement ferme à {conf.end_time().strftime("%H:%M")}'))

        if datetime.combine(date.today(), datetime.now().time()) < datetime.combine(self.date, self.start_time):
            raise ValidationError(_('Les informations de date et d\'heure sont passées'))

        event_start = datetime.combine(self.date, self.start_time)
        event_end = event_start + self.duration

        for occupancy in Occupancy.objects.all().filter(room=self.room, date__gte=self.date,
                                                        date__lt=self.date + timedelta(days=1)):
            occupancy_start = datetime.combine(occupancy.date, occupancy.start_time)
            occupancy_end = occupancy_start + occupancy.duration
            if event_start < occupancy_start > event_end:
                raise ValidationError(_(
                    f'Cet salle est déjà prise de '
                    f'{occupancy_start.strftime("%H:%M")} à {occupancy_end.strftime("%H:%MM")}'))

            if occupancy_start < event_end < occupancy_end:
                raise ValidationError(_(
                    f'Cet salle est déjà prise de '
                    f'{occupancy_start.strftime("%H:%M")} à {occupancy_end.strftime("%H:%MM")}'))

    def save(self, *args, **kwargs):
        self.__validate_fields()
        super(Occupancy, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.room} {self.start_time} {self.duration}'

    def __repr__(self):
        return f'{self.room} {self.start_time} {self.duration}'

    class Meta:
        verbose_name = _('Occupation')
        verbose_name_plural = _('Occupations')
        unique_together = [('room', 'date', 'start_time', 'duration',), ]


class TeacherOccupancy(Model):
    occupancy = ForeignKey(Occupancy, on_delete=CASCADE, verbose_name=_('Occupation'), null=False)
    teacher = ForeignKey(Teacher, on_delete=CASCADE, verbose_name=_('Intervenant'), null=False)

    def save(self, *args, **kwargs):
        super(TeacherOccupancy, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.teacher} {self.teacher} {self.occupancy}'

    class Meta:
        verbose_name = _('Intervenant')
        verbose_name_plural = _('Intervenants')
        unique_together = [('occupancy', 'teacher',), ]


class ClassOccupancy(Model):
    occupancy = ForeignKey(Occupancy, on_delete=CASCADE, verbose_name=_('Occupancy'), null=False)
    _class = ForeignKey(Class, on_delete=CASCADE, verbose_name=_('Class'), null=False)

    def save(self, *args, **kwargs):
        super(ClassOccupancy, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self._class} {self.occupancy}'

    class Meta:
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')
        unique_together = [('occupancy', '_class',), ]
