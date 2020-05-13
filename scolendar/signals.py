from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Student, StudentClassTemp, Subject, StudentSubject


@receiver(post_save, sender=Student)
def student_class_signal(instance, created=False, **kwargs):
    if not created:
        temp = StudentClassTemp.objects.get(student_id=instance.id)
        if temp.class_to_remove:
            instance.groups.remove(temp.class_to_remove)
            temp.class_to_remove.user_set.remove(instance)
        instance.groups.add(temp.class_to_add)
        temp.class_to_add.user_set.add(instance)
        temp.delete()
    return instance


@receiver(post_save, sender=Student)
def attribute_group_to_student(instance, created=False, **kwargs):
    if created:
        for subject in instance._class.subject_set.all():
            student_subject = StudentSubject(
                subject=subject,
                student=instance,
            )
            student_subject.save()
            from scolendar.groups import attribute_student_groups
            attribute_student_groups(subject)
    return instance


@receiver(post_delete, sender=Student)
@receiver(post_delete, sender=StudentSubject)
def student_group_reorganization(sender, instance, **kwargs):
    if sender is Student:
        subjects = Subject.objects.filter(_class=instance._class)
    elif sender is StudentSubject:
        subjects = Subject.objects.filter(id=instance.id)
    else:
        return instance
    for s in subjects:
        from scolendar.groups import attribute_student_groups
        attribute_student_groups(s)
    return instance


@receiver(post_save, sender=StudentSubject)
def student_group_reorganization_on_student_subject(instance, created=False, **kwargs):
    if created:
        subjects = Subject.objects.filter(id=instance.id)
        for s in subjects:
            from scolendar.groups import attribute_student_groups
            attribute_student_groups(s)
    return instance
