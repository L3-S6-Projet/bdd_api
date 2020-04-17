from django.contrib import admin

from .models import Class, Occupancy, ClassOccupancy, TeacherOccupancy, Rooms, Subject, ClassStudent


class StudentInline(admin.TabularInline):
    model = ClassStudent
    extra = 1
    can_delete = True


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'year',
    ]

    fieldsets = [
        (None, {'fields': ['year', 'name', ], })
    ]

    inlines = [
        StudentInline,
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
