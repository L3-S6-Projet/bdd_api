from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Student, StudentClassTemp


@receiver(post_save, sender=Student)
def student_class_signal(sender, instance, update_fields=None, **kwargs):
    try:
        temp = StudentClassTemp.objects.get(student_id=instance.id)
        if temp.class_to_remove:
            instance.groups.remove(temp.class_to_remove)
            temp.class_to_remove.user_set.remove(instance)
        instance.groups.add(temp.class_to_add)
        temp.class_to_add.user_set.add(instance)
        temp.delete()
    except StudentClassTemp.DoesNotExist:
        return instance


@receiver(post_delete, sender=Student)
def student_group_reorganization(sender, instance, update_fields=None, **kwargs):
    pass
