import datetime as dt
from datetime import date, timedelta, datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Model, CharField, IntegerField, ForeignKey, DateField, \
    TimeField, DurationField, CASCADE
from django.utils.translation import gettext as _

from conf import conf
from .validators import start_time_validator, max_duration_validation, teacher_validator, student_validator

years = [
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

session_types = [
    ('CM', _('CM')),
    ('TD', _('TD')),
    ('TP', _('TP')),
]


class Class(Model):
    name = CharField(max_length=255, verbose_name=_('Nom'), null=False)
    year = CharField(max_length=2, verbose_name=_('Année'), choices=years, null=False)

    def save(self, *args, **kwargs):
        super(Class, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.year} {self.name}'

    def __repr__(self):
        return f'{self.year} {self.name}'

    class Meta:
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')
        unique_together = [('name', 'year',), ]


class ClassStudent(Model):
    _class = ForeignKey(Class, on_delete=CASCADE)
    student = ForeignKey(User, verbose_name=_('Student'), on_delete=CASCADE, validators=[student_validator])

    def save(self, *args, **kwargs):
        super(ClassStudent, self).save(*args, **kwargs)

    def __str__(self):
        return self._class.name

    def __repr__(self):
        return self._class.name

    class Meta:
        verbose_name = _('Student')
        verbose_name_plural = _('Students')


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
    duration = DurationField(verbose_name=_('Durée'), null=False, validators=[max_duration_validation],
                             default=timedelta(days=0, hours=1, minutes=0, seconds=0))
    subject = ForeignKey(Subject, on_delete=CASCADE, verbose_name=_('Matière'), null=False)
    session_type = CharField(max_length=2, verbose_name=_('Type'), null=False, choices=session_types)

    def clean(self):
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
        super(Occupancy, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        super(Occupancy, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.room} {self.start_time} {self.duration}'

    def __repr__(self):
        return f'{self.room} {self.start_time} {self.duration}'

    class Meta:
        verbose_name = _('Occupation')
        verbose_name_plural = _('Occupations')
        unique_together = [('room', 'date', 'start_time', 'duration',), ]


def occupancy_overlap_validator_for(o, model):
    occupancy_start = datetime.combine(o.occupancy.date, o.occupancy.start_time)
    occupancy_end = occupancy_start + o.occupancy.duration

    def __overlap_validation_error(overlap_start, overlap_end):
        if model == TeacherOccupancy:
            error_message = _(f'Cet intervenant est déjà occupé '
                              f'de {overlap_start.strftime("%H:%M")} '
                              f'à {overlap_end.strftime("%H:%M")}')
        else:
            error_message = _(
                f'Cette classe est déjà occupée '
                f'de {overlap_start.strftime("%H:%M")} '
                f'à {overlap_end.strftime("%H:%M")}')
        raise ValidationError(error_message)

    for teacher_occupancy in model.objects.all().filter(obj=o.obj, occupancy__date=o.occupancy.date):
        occupancy_object = teacher_occupancy.occupancy
        occupancy_object_start = datetime.combine(occupancy_object.date, occupancy_object.start_time)
        occupancy_object_end = occupancy_object_start + occupancy_object.duration

        if occupancy_object_start < occupancy_start < occupancy_object_end:
            __overlap_validation_error(occupancy_object_start, occupancy_object_end)
        if occupancy_start < occupancy_object_start < occupancy_end:
            __overlap_validation_error(occupancy_start, occupancy_end)


class TeacherOccupancy(Model):
    obj = ForeignKey(User, on_delete=CASCADE, verbose_name=_('Intervenant'), null=False, validators=[teacher_validator])
    occupancy = ForeignKey(Occupancy, on_delete=CASCADE, verbose_name=_('Occupation'), related_name='teachers',
                           null=False)

    def clean(self):
        occupancy_overlap_validator_for(self, TeacherOccupancy)
        super(TeacherOccupancy, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        super(TeacherOccupancy, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.obj} {self.obj} {self.occupancy}'

    class Meta:
        verbose_name = _('Intervenant')
        verbose_name_plural = _('Intervenants')
        unique_together = [('occupancy', 'obj',), ]


class ClassOccupancy(Model):
    occupancy = ForeignKey(Occupancy, on_delete=CASCADE, verbose_name=_('Occupancy'), related_name='classes',
                           null=False)
    obj = ForeignKey(Class, on_delete=CASCADE, verbose_name=_('Class'), null=False)

    def clean(self):
        occupancy_overlap_validator_for(self, ClassOccupancy)
        super(ClassOccupancy, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        super(ClassOccupancy, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.obj} {self.occupancy}'

    class Meta:
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')
        unique_together = [('occupancy', 'obj',), ]
