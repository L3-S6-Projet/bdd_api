from django.conf.urls import url

from scolendar.views import *

urlpatterns = [
    url(r'session$', AuthViewSet.as_view()),

    url(r'profile$', ProfileViewSet.as_view()),

    url(r'teachers$', TeacherViewSet.as_view()),
    url(r'teachers/(?P<teacher_id>[0-9]+)$', TeacherDetailViewSet.as_view()),
    url(r'teachers/(?P<teacher_id>[0-9]+)/occupancies$', TeacherOccupancyDetailViewSet.as_view()),
    url(r'teachers/(?P<teacher_id>[0-9]+)/subjects$', TeacherSubjectDetailViewSet.as_view()),

    url(r'classrooms$', ClassroomViewSet.as_view()),
    url(r'classrooms/(?P<classroom_id>[0-9]+)$', ClassroomDetailViewSet.as_view()),
    url(r'classrooms/(?P<classroom_id>[0-9]+)/occupancies$', ClassroomOccupancyViewSet.as_view()),

    url(r'students$', StudentViewSet.as_view()),
]
