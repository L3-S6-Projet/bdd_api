from django.contrib.auth.models import User
from django.db.models import Model, CharField, IntegerField, ForeignKey, DateField, TimeField, DurationField, CASCADE
from django.utils.translation import gettext as _

from .validators import start_time_validator, end_time_validator

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


class Teacher(User):
    grade = CharField(max_length=4, verbose_name=_('Grade'), choices=grades, null=False)


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


class StudentClasses(Model):
    _class = ForeignKey(Class, on_delete=CASCADE, verbose_name=_('Classe'), null=False)
    student = ForeignKey(Student, on_delete=CASCADE, verbose_name=_('Étudiant'), null=False)

    def save(self, *args, **kwargs):
        super(StudentClasses, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self._class} {self.student}'

    class Meta:
        verbose_name = _('Groupe Etudiant')
        verbose_name_plural = _('Groupe Etudiants')
        unique_together = [('_class', 'student',), ]


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


class Occupancy(Model):
    room = ForeignKey(Rooms, on_delete=CASCADE, verbose_name=_('Salle'), null=False)
    date = DateField(verbose_name=_('Date'), null=False)
    start_time = TimeField(verbose_name=_('Début'), null=False, validators=[start_time_validator, ])
    duration = DurationField(verbose_name=_('Durée'), null=False)

    def clean(self, *args, **kwargs):
        end_time_validator(self.date, self.start_time, self.duration)

    def save(self, *args, **kwargs):
        super(Occupancy, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.room} {self.start_time} {self.duration}'

    def __repr__(self):
        return f'{self.room} {self.start_time} {self.duration}'

    class Meta:
        verbose_name = _('Occupation')
        verbose_name_plural = _('Occupations')
        unique_together = [('room', 'start_time', 'duration',), ]


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
