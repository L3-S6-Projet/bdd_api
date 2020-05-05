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

    url(r'class$', ClassViewSet.as_view()),
    url(r'class/(?P<class_id>[0-9]+)$', ClassDetailViewSet.as_view()),
    url(r'class/(?P<class_id>[0-9]+)/occupancies$', ClassOccupancyViewSet.as_view()),

    url(r'students$', StudentViewSet.as_view()),
    url(r'students/(?P<student_id>[0-9]+)$', StudentDetailViewSet.as_view()),
    url(r'students/(?P<student_id>[0-9]+)/occupancies$', StudentOccupancyDetailViewSet.as_view()),
    url(r'students/(?P<student_id>[0-9]+)/subjects$', StudentSubjectDetailViewSet.as_view()),

    url(r'subjects$', SubjectViewSet.as_view()),
    url(r'subjects/(?P<subject_id>[0-9]+)$', SubjectDetailViewSet.as_view()),
    url(r'subjects/(?P<subject_id>[0-9]+)/occupancies$', SubjectOccupancyViewSet.as_view()),
    url(r'subjects/(?P<subject_id>[0-9]+)/teachers$', SubjectTeacherViewSet.as_view()),
    url(r'subjects/(?P<subject_id>[0-9]+)/groups$', SubjectGroupViewSet.as_view()),
    url(r'subjects/(?P<subject_id>[0-9]+)/groups/(?P<group_id>[0-9]+)/occupancies$',
        SubjectGroupOccupancyViewSet.as_view()),

    url(r'occupancies$', OccupancyViewSet.as_view()),
    url(r'occupancies/(?P<occupancy_id>[0-9]+)$', OccupancyDetailViewSet.as_view()),
]
