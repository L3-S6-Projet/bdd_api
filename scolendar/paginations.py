from rest_framework.pagination import PageNumberPagination

DEFAULT_PAGE = 1


class StudentResultSetPagination(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = 10
    max_page_size = 1000
    page_query_param = 'page'


class TeacherResultSetPagination(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = 10
    max_page_size = 1000
    page_query_param = 'page'


class ClassroomResultSetPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 1000
    page_query_param = 'page'


class ClassResultSetPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 1000
    page_query_param = 'page'


class SubjectResultSetPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 1000
    page_query_param = 'page'
