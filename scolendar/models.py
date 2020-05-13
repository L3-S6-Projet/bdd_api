from datetime import timedelta

from django.contrib.auth.models import Group as BaseGroup, User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext as _
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.models import Token

from .validators import start_datetime_validator, max_duration_validator, phone_number_validator, class_name_validator, \
    end_datetime_validator

levels = ['L1', 'L2', 'L3', 'M1', 'M2', ]
level_list = [(x, _(x)) for x in levels]

ranks = ['MACO', 'PROF', 'PRAG', 'PAST', 'ATER', 'MONI', ]
rank_list = [(x, _(x)) for x in ranks]

occupancy_list = ['CM', 'TD', 'TP', 'PROJ', 'ADM', 'EXT', ]
occupancy_type_list = [(x, _(x)) for x in occupancy_list]

modification_list = ['INSERT', 'EDIT', 'DELETE']
modification_types_list = [(x, _(x)) for x in modification_list]


class Class(BaseGroup):  # registered
    level = models.CharField(max_length=2, verbose_name=_('Niveau'), choices=level_list)

    def clean(self):
        class_name_validator(self.name)
        super(Class, self).clean()

    class Meta:
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')


class Subject(models.Model):  # registered
    _class = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name=_('Classe'))
    name = models.CharField(max_length=255, verbose_name=_('Matière'))
    group_count = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Nombre de groupes'),
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100),
        ]
    )

    def __str__(self):
        return f'{self._class}: {self.name}'

    class Meta:
        verbose_name = _('Matière')
        verbose_name_plural = _('Matières')
        unique_together = [('_class', 'name',), ]


class Student(User):  # registered
    _class = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name=_('Classe'))

    def save(self, *args, **kwargs):
        try:
            old_instance = Student.objects.get(id=self.id)
            super(Student, self).save(*args, **kwargs)
            if old_instance._class != self._class:
                temp = StudentClassTemp(student=self, class_to_remove=old_instance._class,
                                        class_to_add=self._class)
                temp.save()
            return self
        except Student.DoesNotExist:
            super(Student, self).save(*args, **kwargs)
            temp = StudentClassTemp(student=self, class_to_remove=None, class_to_add=self._class)
            temp.save()
            return self

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


class StudentSubject(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name=_('Sujet'))
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name=_('Etudiant'))
    group_number = models.PositiveIntegerField(
        verbose_name=_('Numéro de groupe'),
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100),
        ]
    )

    def clean(self):
        super(StudentSubject, self).clean()
        if self.group_number > self.subject.group_count:
            raise ValidationError(_('Numéro de groupe invalide'))

    class Meta:
        verbose_name = _('Répartition des étudiants en groupe')
        verbose_name_plural = _('Répartitions des étudiants en groupes')


class StudentClassTemp(models.Model):  # should not be registered
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_to_remove = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_to_remove')
    class_to_add = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_to_add')


class Classroom(models.Model):  # registered
    name = models.CharField(max_length=255, verbose_name=_('Nom'), unique=True)
    capacity = models.IntegerField(verbose_name=_('Capacité'))

    def __str__(self):
        return self.name

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


class TeacherSubject(models.Model):  # registered
    teacher = models.OneToOneField(Teacher, on_delete=models.CASCADE, verbose_name=_('Intervenant'), primary_key=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name=_('Matière'))
    in_charge = models.BooleanField(verbose_name=_('Responsable'), default=False)

    class Meta:
        verbose_name = _('Enseignement')
        verbose_name_plural = _('Enseignements')
        unique_together = [('teacher', 'subject')]


class Occupancy(models.Model):  # registered
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name=_('Salle'))
    group_number = models.PositiveIntegerField(verbose_name=_('Numéro du groupe'), blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name=_('Matière'))
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name=_('Interevenant'), blank=True)
    start_datetime = models.DateTimeField(verbose_name=_('Date et Heure de début'), default=now,
                                          validators=[start_datetime_validator])
    duration = models.DurationField(verbose_name=_('Durée'), default=timedelta(days=0, hours=1, minutes=0, seconds=0),
                                    validators=[max_duration_validator])
    end_datetime = models.DateTimeField(verbose_name=_('Date et Heure de fin'), validators=[end_datetime_validator])
    occupancy_type = models.CharField(max_length=4, verbose_name=_('Type'), choices=occupancy_type_list, default='CM')
    name = models.CharField(max_length=255, verbose_name=_('Nom'))
    description = models.TextField(verbose_name=_('Description'), default='')
    deleted = models.BooleanField(verbose_name=_('Supprimé'), default=False)

    def clean(self):
        super(Occupancy, self).clean()

        def check(occupancies, error_message):
            for occ in occupancies:
                if occ.id == self.id:
                    continue
                latest_start = max(self.start_datetime, occ.start_datetime)
                earliest_end = min(self.end_datetime, occ.end_datetime)
                delta = (earliest_end - latest_start).days + 1
                overlap = max(0, delta)
                if overlap > 0:
                    raise ValidationError(error_message)

        def check_room_occupied():
            if self.classroom:
                occupancies = Occupancy.objects.filter(classroom=self.classroom, deleted=False,
                                                       start_datetime__day=self.start_datetime.day)
                check(occupancies, _('Cette salle est déjà réservée'))

        def check_teacher_occupied():
            occupancies = Occupancy.objects.filter(teacher=self.teacher, deleted=False,
                                                   start_datetime__day=self.start_datetime.day)
            check(occupancies, _('L\'enseignant est déjà occupé'))

        def check_group_occupied():
            if self.group_number:
                occupancies = Occupancy.objects.filter(group_number=self.group_number, deleted=False,
                                                       start_datetime__day=self.start_datetime.day)
                check(occupancies, _('Ce groupe est déjà occupé'))
            else:
                occupancies = Occupancy.objects.filter(subject___class=self.subject._class, deleted=False,
                                                       start_datetime__day=self.start_datetime.day)
                check(occupancies, _('Cette classe est déjà occupée'))

        # TODO check if one student is in another group which is occupied
        check_room_occupied()
        check_teacher_occupied()
        check_group_occupied()

    def save(self, *args, **kwargs):
        self.end_datetime = self.start_datetime + self.duration
        self.clean()
        try:
            old_instance = Occupancy.objects.get(id=self.id)
            super(Occupancy, self).save(*args, **kwargs)
            if not old_instance.deleted and not self.deleted:
                occupancy_modification = OccupancyModification(
                    occupancy=self,
                    modification_type='EDIT',
                    previous_start_datetime=old_instance.start_datetime,
                    previous_duration=old_instance.duration,
                    new_start_datetime=self.start_datetime,
                    new_duration=self.duration
                )
                occupancy_modification.save()
            elif not old_instance.deleted and self.deleted:
                occupancy_modification = OccupancyModification(
                    occupancy=self,
                    modification_type='DELETE',
                    previous_start_datetime=old_instance.start_datetime,
                    previous_duration=old_instance.duration,
                )
                occupancy_modification.save()
        except Occupancy.DoesNotExist:
            super(Occupancy, self).save(*args, **kwargs)
            occupancy_modification = OccupancyModification(
                occupancy=self,
                modification_type='INSERT',
                new_start_datetime=self.start_datetime,
                new_duration=self.duration,
            )
            occupancy_modification.save()

    class Meta:
        verbose_name = _('Occupation')
        verbose_name_plural = _('Occupations')
        unique_together = [('classroom', 'subject', 'teacher', 'start_datetime')]


class OccupancyModification(models.Model):
    occupancy = models.ForeignKey(Occupancy, on_delete=models.CASCADE, verbose_name=_('Occupation'))
    modification_type = models.CharField(max_length=6, verbose_name=_('Type'), choices=modification_types_list)
    previous_start_datetime = models.DateTimeField(verbose_name=_('Ancienne date de début'), blank=True, null=True)
    previous_duration = models.DurationField(verbose_name=_('Ancienne durée'), blank=True, null=True)
    new_start_datetime = models.DateTimeField(verbose_name=_('Nouvelle date de début'), blank=True, null=True)
    new_duration = models.DurationField(verbose_name=_('Nouvelle durée'), blank=True, null=True)
    modification_date = models.DateTimeField(verbose_name=_('Date de modification'), auto_now=True)


class ICalToken(Token):
    class Meta:
        verbose_name = _('Token iCal')
        verbose_name_plural = _('Tokens iCal')
