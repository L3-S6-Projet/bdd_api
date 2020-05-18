from scolendar.models import StudentSubject, Subject


def attribute_student_groups(subject: Subject) -> None:
    """
    Automatically distribute students in groups

    The algorithm is quite basic:
    - We get all the students registered for the subject
    - Calculate the group sizes
    - Distribute the students in alphabetical order in the appropriate number of groups

    :param subject: The subject where we need to distribute students in groups
    :return: None
    """
    student_subjects = StudentSubject.objects.filter(subject=subject)
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


def group_size(group_number: int) -> int:
    """
    Get the number of students in a group

    :param group_number: The group number for which we want the number of students
    :return: The group size
    """
    return len(StudentSubject.objects.filter(group_number=group_number))
