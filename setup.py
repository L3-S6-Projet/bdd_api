import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.db.utils import IntegrityError
from pytz import timezone

from scolendar.groups import attribute_student_groups
from scolendar.models import Student, Class, Teacher, Classroom, Subject, Occupancy, StudentSubject
from scolendar.signals import attribute_group_to_student, student_class_signal, \
    student_group_reorganization_on_student_subject
import time

User = get_user_model()
occupancy_types = {
    'CM': 'CM',
    'TD': 'TD',
    'TP': 'TP',
    'Projet': 'PROJ',
    'Administration': 'ADM',
    'External': 'EXT'
}


def create_super():
    try:
        User.objects.create_superuser('super', 'super@test.com', 'passwdtest')
    except IntegrityError:
        pass


def create_admin():
    try:
        user = User.objects.create_user('admin', 'admin@test.com', 'passwdtest')
        user.is_staff = True
        user.save()
    except IntegrityError:
        pass


def create_class() -> Class:
    try:
        created_class = Class(name='L3 Informatique', level='L3')
        created_class.save()
    except IntegrityError:
        created_class = Class.objects.get(name='L3 Informatique', level='L3')
    return created_class


def create_students(_class: Class):
    with open('sample_data/students.json') as student_file:
        student_json = json.load(student_file)
        subjects = _class.subject_set.all()
        for student_entry in student_json:
            f_name = student_entry['first_name']
            l_name = student_entry['last_name']
            print(f'Creating Student: {f_name} {l_name}')
            try:
                student = Student(
                    username=f'{f_name.lower().replace(" ", "")}.{l_name.lower().replace(" ", "")}',
                    _class=_class,
                    first_name=f_name,
                    last_name=l_name,
                )
                student.set_password('passwdtest')
                student.save()
                for subject in subjects:
                    student_subject = StudentSubject(subject=subject, student=student)
                    student_subject.save()
            except IntegrityError:
                pass


def create_teachers(f_name: str, l_name: str) -> Teacher:
    print(f'Creating Teacher: {f_name} {l_name}')
    try:
        teacher = Teacher(
            username=f'{f_name.lower().replace(" ", "")}.{l_name.lower().replace(" ", "")}',
            email=f'{f_name.lower().replace(" ", "-")}.{l_name.lower().replace(" ", "-")}@univ-amu.fr',
            phone_number='06 61 66 16 61',
            first_name=f_name,
            last_name=l_name,
        )
        teacher.set_password('passwdtest')
        teacher.save()
    except IntegrityError:
        teacher = Teacher.objects.get(first_name=f_name, last_name=l_name)
    return teacher


def create_classroom(name: str) -> Classroom:
    try:
        classroom = Classroom(name=name, capacity=50)
        classroom.save()
    except IntegrityError:
        classroom = Classroom.objects.get(name=name)
    return classroom


def create_subject(name: str, _class: Class) -> Subject:
    try:
        subject = Subject(_class=_class, name=name)
        subject.save()
    except IntegrityError:
        subject = Subject.objects.get(name=name, _class=_class)
    return subject


def create_occupancy(start: int, end: int, name: str, description: str, teacher: Teacher, classroom: Classroom,
                     subject: Subject, occ_type: str):
    try:
        o_type = occupancy_types[occ_type]
        start_datetime = datetime.fromtimestamp(start, tz=timezone(settings.TIME_ZONE))
        end_datetime = datetime.fromtimestamp(end, tz=timezone(settings.TIME_ZONE))
        duration = end_datetime - start_datetime
        occupancy = Occupancy(
            classroom=classroom,
            subject=subject,
            teacher=teacher,
            start_datetime=start_datetime,
            duration=duration,
            occupancy_type=o_type,
            name=name,
            description=description
        )
        occupancy.save()
    except IntegrityError:
        pass
    except ValidationError:
        pass


def create_teachers_classrooms_subjects_occupancies():
    with open('sample_data/occupancies.json') as f:
        data = json.load(f)
        for entry in data:
            if entry['professor'] is None:
                continue
            professor = entry['professor'].split(' ', 1)
            teacher_obj = create_teachers(f_name=professor[1], l_name=professor[0])
            classroom_obj = create_classroom(entry['location'])
            subject_obj = create_subject(entry['subject'], _class=_class)
            create_occupancy(
                start=entry['start'],
                end=entry['end'],
                name=entry['name'],
                description=entry['description'],
                teacher=teacher_obj,
                classroom=classroom_obj,
                subject=subject_obj,
                occ_type=entry['type']
            )


def disconnect_triggers():
    post_save.disconnect(receiver=attribute_group_to_student, sender=Student)
    post_save.disconnect(receiver=student_class_signal, sender=Student)
    post_save.disconnect(receiver=student_group_reorganization_on_student_subject, sender=StudentSubject)


def attribute_subject_groups():
    for s in Subject.objects.all():
        print(f'Attributing groups for {s.name}')
        attribute_student_groups(s)


start_time = time.time()
print()
print('Disconnecting signals')
disconnect_triggers()
print()
print('Creating super')
create_super()
print()
print('Creating admin')
create_admin()
print()
print('Creating classes')
_class = create_class()
print()
print('Creating teachers, classrooms, subjects and occupancies')
create_teachers_classrooms_subjects_occupancies()
print()
print('Creating students')
create_students(_class)
print()
print('Attributing groups to students')
attribute_subject_groups()
print("--- %s seconds ---" % (time.time() - start_time))
exit(0)
