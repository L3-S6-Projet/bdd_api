from datetime import timedelta

from django.contrib.auth.models import Group as BaseGroup, User
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext as _

from .validators import start_datetime_validator, max_duration_validator, phone_number_validator, class_name_validator

levels = [
    ('L1', _('L1')),
    ('L2', _('L2')),
    ('L3', _('L3')),
    ('M1', _('M1')),
    ('M2', _('M2')),
]

ranks = ['MACO', 'PROF', 'PRAG', 'PAST', 'ATER', 'MONI', ]

rank_list = [
    ('MACO', _('Maître de conférences')),
    ('PROF', _('Professeur')),
    ('PRAG', _('PRAG')),
    ('PAST', _('PAST')),
    ('ATER', _('ATER')),
    ('MONI', _('Moniteur')),
]

occupancy_list = ['CM', 'TD', 'TP', 'PROJ', 'ADM', 'EXT']

occupancy_type_list = [
    ('CM', _('CM')),
    ('TD', _('TD')),
    ('TP', _('TP')),
]


class Class(BaseGroup):  # registered
    def clean(self):
        class_name_validator(self.name)
        super(Class, self).clean()

    class Meta:
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')


class Subject(models.Model):  # registered
    _class = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name=_('Classe'))
    name = models.CharField(max_length=255, verbose_name=_('Matière'))

    def __str__(self):
        return f'{self._class}: {self.name}'

    class Meta:
        verbose_name = _('Matière')
        verbose_name_plural = _('Matières')
        unique_together = [('_class', 'name',), ]


class Group(BaseGroup):  # registered
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name=_('Matière'))

    class Meta:
        verbose_name = _('Groupe d\'UE')
        verbose_name_plural = _('Groupes d\'UE')


class Student(User):  # registered
    _class = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name=_('Classe'))
    student_groups = models.ManyToManyField(Group, verbose_name=_('Groupes'), blank=True,
                                            help_text=_('Les groupes auxquels l\'étudiant appartient'),
                                            related_name='student_list', related_query_name='student')

    def __init__(self, *args, **kwargs):
        super(Student, self).__init__(*args, **kwargs)
        self.__important_fields = ['_class']
        for field in self.__important_fields:
            setattr(self, '__original_%s' % field, getattr(self, field, None))

    def has_changed(self):
        for field in self.__important_fields:
            orig = '__original_%s' % field
            if getattr(self, orig) != getattr(self, field):
                return True
        return False

    def save(self, *args, **kwargs):
        if self.has_changed():
            if getattr(self, '__original_%s' % '_class', None) != self._class:
                setattr(self, '__original_%s' % '_class', self._class)
        super(Student, self).save(*args, **kwargs)

    def __str__(self):
        if len(self.first_name) > 0 and len(self.last_name) > 0:
            return f'{self.first_name} {self.last_name}'.title()
        elif len(self.first_name) > 0:
            return self.first_name
        elif len(self.last_name) > 0:
            return self.last_name
        else:
            return self.username

    class Meta(User.Meta):
        verbose_name = _('Etudiant')
        verbose_name_plural = _('Etudiants')


class StudentClassTemp(models.Model):  # should not be registered
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_to_remove = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_to_remove')
    class_to_add = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_to_add')


class Classroom(models.Model):  # registered
    name = models.CharField(max_length=255, verbose_name=_('Nom'), unique=True)
    capacity = models.IntegerField(verbose_name=_('Capacité'))

    class Meta:
        verbose_name = _('Salle')
        verbose_name_plural = _('Salles')
        unique_together = [('name', 'capacity',), ]


class Teacher(User):  # registered
    phone_number = models.CharField(max_length=31, verbose_name=_('Téléphone'), validators=[phone_number_validator, ])
    rank = models.CharField(max_length=4, verbose_name=_('Grade'), choices=rank_list)

    class Meta:
        verbose_name = _('Intervenant')
        verbose_name_plural = _('Intervenants')


class SubjectTeacher(models.Model):  # registered
    teacher = models.OneToOneField(Teacher, on_delete=models.CASCADE, verbose_name=_('Intervenant'), primary_key=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name=_('Matière'))
    in_charge = models.BooleanField(verbose_name=_('Responsable'), default=False)

    class Meta:
        verbose_name = _('Enseignant d\'UE')
        verbose_name_plural = _('Enseignants d\'UE')
        unique_together = [('teacher', 'subject')]


class Occupancy(models.Model):  # registered
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name=_('Salle'))
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name=_('Groupe'))
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name=_('Matière'))
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name=_('Interevenant'))
    start_datetime = models.DateTimeField(verbose_name=_('Date et Heure de début'), default=now,
                                          validators=[start_datetime_validator])
    duration = models.DurationField(verbose_name=_('Durée'), default=timedelta(days=0, hours=1, minutes=0, seconds=0),
                                    validators=[max_duration_validator])
    occupancy_type = models.CharField(max_length=3, verbose_name=_('Type'), choices=occupancy_type_list, default='CM')

    def save(self, *args, **kwargs):
        super(Occupancy, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Occupation')
        verbose_name_plural = _('Occupations')
        unique_together = [('classroom', 'group', 'subject', 'teacher', 'start_datetime')]
