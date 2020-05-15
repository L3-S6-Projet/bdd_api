from django.http import HttpResponse
from ics import Calendar, Event
from ics.attendee import Organizer, Attendee

from scolendar.models import Occupancy, OccupancyModification, ICalToken, Student, Teacher
from scolendar.viewsets.auth_viewsets import AuthViewSet
from scolendar.viewsets.class_viewsets import ClassViewSet, ClassDetailViewSet, ClassOccupancyViewSet
from scolendar.viewsets.classroom_viewsets import ClassroomDetailViewSet, ClassroomOccupancyViewSet, ClassroomViewSet
from scolendar.viewsets.occupancy_viewsets import OccupancyDetailViewSet, OccupancyViewSet
from scolendar.viewsets.profile_viewsets import ProfileViewSet, ProfileLastOccupancyEdit, ProfileICalFeed
from scolendar.viewsets.student_viewsets import StudentDetailViewSet, StudentOccupancyDetailViewSet, \
    StudentSubjectDetailViewSet, StudentViewSet
from scolendar.viewsets.subject_viewsets import SubjectDetailViewSet, SubjectOccupancyViewSet, SubjectTeacherViewSet, \
    SubjectGroupViewSet, SubjectGroupOccupancyViewSet, SubjectViewSet
from scolendar.viewsets.teacher_viewsets import TeacherViewSet, TeacherDetailViewSet, TeacherOccupancyDetailViewSet, \
    TeacherSubjectDetailViewSet

# Session
session = AuthViewSet.as_view()

# Profile
profile = ProfileViewSet.as_view()
profile_occupancy_modifications = ProfileLastOccupancyEdit.as_view()
profile_iCal_feed = ProfileICalFeed.as_view()

# Teachers
teachers = TeacherViewSet.as_view()
teachers_details = TeacherDetailViewSet.as_view()
teacher_occupancies = TeacherOccupancyDetailViewSet.as_view()
teacher_subjects = TeacherSubjectDetailViewSet.as_view()

# Classrooms
classrooms = ClassroomViewSet.as_view()
classroom_details = ClassroomDetailViewSet.as_view()
classrooms_occupancies = ClassroomOccupancyViewSet.as_view()

# Classes
class_ = ClassViewSet.as_view()
class_details = ClassDetailViewSet.as_view()
class_occupancies = ClassOccupancyViewSet.as_view()

# Students
students = StudentViewSet.as_view()
students_details = StudentDetailViewSet.as_view()
students_occupancies = StudentOccupancyDetailViewSet.as_view()
students_subjects = StudentSubjectDetailViewSet.as_view()

# Subjects
subjects = SubjectViewSet.as_view()
subjects_details = SubjectDetailViewSet.as_view()
subjects_occupancies = SubjectOccupancyViewSet.as_view()
subjects_teachers = SubjectTeacherViewSet.as_view()
subjects_groups = SubjectGroupViewSet.as_view()
subjects_groups_occupancies = SubjectGroupOccupancyViewSet.as_view()

# Occupancies
occupancies = OccupancyViewSet.as_view()
occupancies_details = OccupancyDetailViewSet.as_view()


def i_cal_feed(request, token):
    try:
        token = ICalToken.objects.get(pk=token)
        try:
            student = Student.objects.get(id=token.user.id)
            occupancy_list = Occupancy.objects.filter(subject___class=student._class)
        except Student.DoesNotExist:
            try:
                teacher = Teacher.objects.get(id=token.user.id)
                occupancy_list = Occupancy.objects.filter(teacher=teacher)
            except Teacher.DoesNotExist:
                return HttpResponse('Invalid token', status=403)
        calendar = Calendar()
        for occ in occupancy_list:
            occ_mod_created = OccupancyModification.objects.get(occupancy=occ, modification_type='INSERT')
            organizer = Organizer(
                common_name=f'{occ.teacher.first_name} {occ.teacher.last_name}',
                email=occ.teacher.email,
            )
            if occ.group_number:
                attendee_name = f'{occ.subject.name} - Groupe {occ.group_number}'
            else:
                attendee_name = f'{occ.subject._class.name}'
            attendees = [
                Attendee(
                    common_name=attendee_name,
                    email='',
                )
            ]
            e = Event(
                name=occ.name,
                begin=occ.start_datetime,
                duration=occ.duration,
                created=occ_mod_created.modification_date,
                location=occ.classroom.name,
                organizer=organizer,
                attendees=attendees,
            )
            occ_last_modification = OccupancyModification.objects.filter(
                occupancy=occ,
                modification_type='EDIT'
            ).order_by('-modification_date')
            if len(occ_last_modification) > 0:
                e.last_modified = occ_last_modification[0].modification_date
            calendar.events.add(e)
        response = HttpResponse(str(calendar), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="calendar.ics"'
        return response
    except ICalToken.DoesNotExist:
        return HttpResponse('Token does not exist', status=403)
