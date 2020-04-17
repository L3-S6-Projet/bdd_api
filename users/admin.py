from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from .models import UserInfo


class UserInline(admin.StackedInline):
    model = UserInfo
    can_delete = False
    verbose_name = _('Type')
    verbose_name_plural = _('Type')


class CustomUserAdmin(BaseUserAdmin):
    inlines = [
        UserInline,
    ]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
