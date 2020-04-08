from django.contrib import admin

from .models import Teacher, Student, Class, Occupancy, ClassOccupancy, TeacherOccupancy, Rooms, Subject


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    pass


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    pass


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'year',
    ]

    fieldsets = [
        (None, {'fields': ['year', 'name', ], })
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
