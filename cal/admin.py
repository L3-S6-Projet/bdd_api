from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext as _

from .models import Class, Occupancy, ClassOccupancy, TeacherOccupancy, Rooms, Subject, CalUser


@admin.register(CalUser)
class CalUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'type')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'type'),
        }),
    )


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'year',
    ]

    fieldsets = [
        (None, {'fields': ['year', 'name', 'student', ], })
    ]


@admin.register(Rooms)
class RoomsAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'capacity',
    ]

    fieldsets = [
        (None, {'fields': ['name', 'capacity', ], })
    ]


class ClassOccupancyInLine(admin.TabularInline):
    model = ClassOccupancy
    extra = 1


class TeacherOccupancyInLine(admin.TabularInline):
    model = TeacherOccupancy
    extra = 1


@admin.register(Occupancy)
class OccupancyAdmin(admin.ModelAdmin):
    list_display = [
        'room',
        'date',
        'start_time',
        'duration',
        'subject',
        'session_type',
    ]

    fieldsets = [
        (None, {'fields': ['room', 'date', 'start_time', 'duration', 'subject', 'session_type', ], })
    ]

    inlines = [
        TeacherOccupancyInLine,
        ClassOccupancyInLine,
    ]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = [
        'name',
    ]

    fieldsets = [
        (None, {'fields': ['name', ], })
    ]
