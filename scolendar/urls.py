from django.conf.urls import url

from scolendar.views import session, profile, profile_occupancy_modifications, profile_next_occupancy, \
    profile_iCal_feed, teachers, teachers_details, teacher_occupancies, teacher_subjects, classrooms, \
    classroom_details, classrooms_occupancies, class_, class_details, class_occupancies, students, students_details, \
    students_occupancies, students_subjects, subjects, subjects_details, subjects_occupancies, subjects_teachers, \
    subjects_groups, subjects_groups_occupancies, occupancies, occupancies_details, i_cal_feed

urlpatterns = [
    url(r'session$', session),

    url(r'profile$', profile),
    url(r'profile/last-occupancies-modifications', profile_occupancy_modifications),
    url(r'profile/next-occupancy', profile_next_occupancy),
    url(r'profile/feeds/ical', profile_iCal_feed),

    url(r'teachers$', teachers),
    url(r'teachers/(?P<teacher_id>[0-9]+)$', teachers_details),
    url(r'teachers/(?P<teacher_id>[0-9]+)/occupancies$', teacher_occupancies),
    url(r'teachers/(?P<teacher_id>[0-9]+)/subjects$', teacher_subjects),

    url(r'classrooms$', classrooms),
    url(r'classrooms/(?P<classroom_id>[0-9]+)$', classroom_details),
    url(r'classrooms/(?P<classroom_id>[0-9]+)/occupancies$', classrooms_occupancies),

    url(r'classes$', class_),
    url(r'classes/(?P<class_id>[0-9]+)$', class_details),
    url(r'classes/(?P<class_id>[0-9]+)/occupancies$', class_occupancies),

    url(r'students$', students),
    url(r'students/(?P<student_id>[0-9]+)$', students_details),
    url(r'students/(?P<student_id>[0-9]+)/occupancies$', students_occupancies),
    url(r'students/(?P<student_id>[0-9]+)/subjects$', students_subjects),

    url(r'subjects$', subjects),
    url(r'subjects/(?P<subject_id>[0-9]+)$', subjects_details),
    url(r'subjects/(?P<subject_id>[0-9]+)/occupancies$', subjects_occupancies),
    url(r'subjects/(?P<subject_id>[0-9]+)/teachers$', subjects_teachers),
    url(r'subjects/(?P<subject_id>[0-9]+)/groups$', subjects_groups),
    url(r'subjects/(?P<subject_id>[0-9]+)/groups/(?P<group_number>[0-9]+)/occupancies$', subjects_groups_occupancies),

    url(r'occupancies$', occupancies),
    url(r'occupancies/(?P<occupancy_id>[0-9]+)$', occupancies_details),

    url(r'feeds/ical/(?P<token>[a-zA-Z0-9]+)$', i_cal_feed),
]
