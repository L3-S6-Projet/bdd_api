from django.contrib.auth.models import AbstractUser, User
from django.db.models import Model, OneToOneField, CharField, CASCADE
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

person_types = [
    ('INT', _('Intervenant')),
    ('STU', _('Étudiant')),
]


class UserInfo(Model):
    user = OneToOneField(User, on_delete=CASCADE)
    type = CharField(max_length=255, verbose_name=_('Type'), null=False, default='STU', choices=person_types)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserInfo.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userinfo.save()
