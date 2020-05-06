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
