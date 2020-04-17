"""from django_ical.views import ICalFeed

from enseign import settings
from .models import Occupancy, Teacher, TeacherOccupancy, Class, Student, ClassOccupancy
from datetime import datetime


class ICalFeedBase (ICalFeed):
    product_id = '-//example.com//Cal//FR'
    timezone = settings.TIME_ZONE
    file_name = "event.ics"


class EventFeed(ICalFeedBase):
    def __call__(self, request, *args, **kwargs):
        self.request = request
        return super(EventFeed, self).__call__(request, *args, **kwargs)

    def items(self):
        teacher = Teacher.objects.filter(id=self.request.user.id)
        if teacher:
            return TeacherOccupancy.objects.filter(obj=self.request.id).select_related().order_by('-date').order_by(
                '-start_time')

        student = Student.objects.filter(id=self.request.user.id)
        if student:
            return ClassOccupancy.objects.filter(obj=student.student_class.id).select_related().order_by(
                '-date').order_by('-start_time')
        return Occupancy.objects.all().order_by('-start_time')

    def item_guid(self, item):
        return f'{item.id}'

    def item_title(self, item):
        return f'{item.subject.name}-{item.session_type}'

    def item_description(self, item):
        return item.room.name

    def item_start_datetime(self, item):
        return datetime.combine(item.date, item.start_time)

    def item_end_datetime(self, item):
        return self.item_start_datetime(item) + item.duration
"""
