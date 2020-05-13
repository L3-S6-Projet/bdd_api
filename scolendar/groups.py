from scolendar.models import StudentSubject, Subject


def attribute_student_groups(subject: Subject):
    student_subjects = StudentSubject.objects.filter(subject=subject).order_by('student__last_name',
                                                                               'student__first_name')
    nb_students_in_subject = len(student_subjects)
    computed_group_size = nb_students_in_subject // subject.group_count + 1
    counter = 0
    current_group = 1
    for ss in student_subjects:
        if counter > computed_group_size:
            counter = 0
            current_group += 1
        ss.group_number = current_group
        counter += 1
        ss.save()


def group_size(group_number: int):
    return len(StudentSubject.objects.filter(group_number=group_number))
