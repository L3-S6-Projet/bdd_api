from django.conf.urls import url

from cal.views import ClassList, RoomList, SubjectList, OccupancyList, TeacherOccupancyList, ClassOccupancyList

urlpatterns = [
    url(r'^classes/$', ClassList.as_view()),
    url(r'^rooms/$', RoomList.as_view()),
    url(r'^subjects/$', SubjectList.as_view()),
    url(r'^occupancies/$', OccupancyList.as_view()),
    url(r'^teacher_occupancies/$', TeacherOccupancyList.as_view()),
    url(r'^class_occupancies/$', ClassOccupancyList.as_view()),
]
