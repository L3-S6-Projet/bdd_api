from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.functions import Trunc
from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_ARRAY, TYPE_INTEGER, TYPE_STRING, \
    TYPE_BOOLEAN, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from pytz import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.models import Student, Class, StudentSubject, Occupancy, TeacherSubject, Teacher
from scolendar.paginations import StudentResultSetPagination
from scolendar.serializers import StudentCreationSerializer, StudentSerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin
from scolendar.viewsets.common.schemas import teacher_list_schema, occupancies_schema


class StudentViewSet(GenericAPIView, TokenHandlerMixin):
    serializer_class = StudentSerializer
    queryset = Student.objects.all().order_by('id')
    pagination_class = StudentResultSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('query', None)
        if query:
            if len(query) >= 3:
                queryset = queryset.filter(
                    Q(first_name__unaccent__icontains=query) |
                    Q(last_name__unaccent__icontains=query) |
                    Q(_class__name__unaccent__icontains=query)
                )
        return queryset

    @swagger_auto_schema(
        operation_summary='Returns a paginated list of all students.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              '10 students should be returned per page. At least three characters should be provided '
                              'for the search.',
        responses={
            200: Response(
                description='A list of all students.',
                schema=Schema(
                    title='StudentListResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING,
                                         example='success'),
                        'total': Schema(type=TYPE_INTEGER,
                                        description='Total number of students',
                                        example=166),
                        'students': Schema(type=TYPE_ARRAY,
                                           items=Schema(
                                               type=TYPE_OBJECT,
                                               properties={
                                                   'id': Schema(
                                                       type=TYPE_INTEGER,
                                                       example=166),
                                                   'first_name': Schema(
                                                       type=TYPE_STRING,
                                                       example='John'),
                                                   'last_name': Schema(
                                                       type=TYPE_STRING,
                                                       example='Doe'),
                                                   'class_name': Schema(
                                                       type=TYPE_STRING,
                                                       example='L3 INFORMATIQUE'),
                                               }, required=['id',
                                                            'first_name',
                                                            'last_name',
                                                            'class_name', ]), ),
                    },
                    required=['status', 'total', 'students', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InvalidCredentials',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InsufficientAuthorization',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Students'],
        manual_parameters=[
            Parameter(name='query', in_=IN_QUERY, type=TYPE_STRING, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                result = self.get_paginated_response(serializer.data)
                response = result.data
            else:
                serializer = self.get_serializer(queryset, many=True)
                response = serializer.data
            data = {
                'status': 'success',
                'total': response['count'],
                'students': response['results'],
            }
            return RF_Response(data)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except NotFound:
            data = {
                'status': 'success',
                'total': len(self.get_queryset()),
                'teachers': [],
            }
            return RF_Response(data)

    @swagger_auto_schema(
        operation_summary='Creates a new student.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'This should trigger the re-organization of groups.',
        responses={
            201: Response(
                description='Student created',
                schema=Schema(
                    title='AccountCreatedResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING,
                                         example='success'),
                        'username': Schema(type=TYPE_STRING,
                                           example='azure_diamong'),
                        'password': Schema(type=TYPE_STRING,
                                           example='aBcD1234'),
                    },
                    required=['status', 'username', 'password', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InvalidCredentials',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InsufficientAuthorization',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidID', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),

        },
        tags=['Students'],
        request_body=Schema(
            title='StudentCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'first_name': Schema(type=TYPE_STRING, example='John'),
                'last_name': Schema(type=TYPE_STRING, example='Doe'),
                'class_id': Schema(type=TYPE_INTEGER, example=166),
            }, required=['first_name', 'last_name', 'class_id', ]
        )
    )
    def post(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            serializer = StudentCreationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return RF_Response(serializer.data, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Deletes the given students using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'This request should trigger the re-organization of students in the affected groups.',
        responses={
            200: Response(
                description='Data deleted',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'success': Schema(
                            type=TYPE_STRING,
                            example='success'),
                    },
                    required=['success', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InsufficientAuthorization',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InsufficientAuthorization',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Students'],
        request_body=Schema(
            title='IDRequest',
            type=TYPE_ARRAY,
            items=Schema(
                type=TYPE_INTEGER,
                example=166
            )
        ),
    )
    def delete(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)

            def delete_student(student_id: int):
                student = Student.objects.get(id=student_id)
                student.delete()

            for post_id in request.data:
                try:
                    delete_student(post_id)
                except Student.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)

            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class StudentDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets information for a student.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Student information',
                schema=Schema(
                    title='StudentResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'student': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                'first_name': Schema(type=TYPE_STRING, example='John'),
                                'last_name': Schema(type=TYPE_STRING, example='Doe'),
                                'username': Schema(type=TYPE_STRING, example='road_buddy'),
                                'total_hours': Schema(type=TYPE_INTEGER, example=166),
                                'subjects': Schema(
                                    type=TYPE_ARRAY,
                                    items=Schema(
                                        type=TYPE_OBJECT,
                                        properties={
                                            'name': Schema(type=TYPE_STRING, example='Anglais'),
                                            'group': Schema(type=TYPE_STRING, example='Groupe 1'),
                                        },
                                        required=[
                                            'name',
                                            'group',
                                        ]
                                    )
                                )
                            },
                            required=[
                                'first_name',
                                'last_name',
                                'username',
                                'total_hours',
                                'subjects',
                            ]
                        ),
                    },
                    required=['status', 'student', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InsufficientAuthorization', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidID', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Students', ]
    )
    def get(self, request, student_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                student = Student.objects.get(id=student_id)

                def get_subjects() -> list:
                    subject_list = []
                    student_subjects = StudentSubject.objects.filter(student=student)
                    # TODO check this shit
                    for s in student_subjects:
                        subject_list.append(
                            {
                                'name': s.subject.name,
                                'group': s.group_number,
                            }
                        )
                    return subject_list

                subjects = get_subjects()

                def count_hours() -> int:
                    total = 0
                    return total

                student = {
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'username': student.username,
                    'total_hours': count_hours(),
                    'subjects': subjects,
                }
                return RF_Response({'status': 'success', 'student': student})
            except Student.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Updates information for a student.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'Only filled fields should be updated.',
        responses={
            200: Response(
                description='Student updated',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success')
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InsufficientAuthorization', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidID', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Password too simple (code=`PasswordTooSimple`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
        },
        tags=['Students', ],
        request_body=Schema(
            title='StudentUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'first_name': Schema(type=TYPE_STRING, example='John'),
                'last_name': Schema(type=TYPE_STRING, example='Doe'),
                'class_id': Schema(type=TYPE_INTEGER, example=166),
                'password': Schema(type=TYPE_STRING, example='new_password'),
            }
        )
    )
    def put(self, request, student_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                student = Student.objects.get(id=student_id)
                data = request.data
                data_keys = data.keys()
                if 'first_name' in data_keys:
                    student.first_name = data['first_name']
                if 'last_name' in data_keys:
                    student.last_name = data['last_name']
                if 'class_id' in data_keys:
                    try:
                        _class = Class.objects.get(id=data['class_id'])
                        student._class = _class
                    except Class.DoesNotExist:
                        return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
                if 'password' in data_keys:
                    try:
                        validate_password(data['new_password'])
                        student.set_password(data['new_password'])
                    except ValidationError:
                        return RF_Response({'status': 'error', 'code': 'PasswordTooSimple'},
                                           status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                student.save()
                return RF_Response({'status': 'success'})
            except Student.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class StudentOccupancyDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a student for the given time period.',
        operation_description='Note : only users with the role `administrator`, or students whose id match the one in '
                              'the URL should be able to access this route.',
        responses={
            200: Response(
                description='Student occupancies',
                schema=occupancies_schema
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InsufficientAuthorization', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidID', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Students', 'role-student', ],
        manual_parameters=[
            Parameter(
                name='start',
                description='Start timestamp of the occupancies',
                in_=IN_QUERY,
                type=TYPE_INTEGER,
                required=False,
            ),
            Parameter(
                name='end',
                description='End timestamp of the occupancies',
                in_=IN_QUERY,
                type=TYPE_INTEGER,
                required=False
            ),
            Parameter(
                name='occupancies_per_day',
                description='Pass 0 to return ALL the events',
                in_=IN_QUERY,
                type=TYPE_INTEGER,
                required=False
            ),
        ],
    )
    def get(self, request, student_id):
        try:
            token = self._get_token(request)
            try:
                Teacher.objects.get(id=token.user_id)
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            except Teacher.DoesNotExist:
                try:
                    student = Student.objects.get(id=student_id)

                    def get_days() -> list:
                        start_timestamp = request.query_params.get('start', None)
                        end_timestamp = request.query_params.get('end', None)
                        nb_per_day = int(request.query_params.get('occupancies_per_day', 0))
                        days = []
                        occ = Occupancy.objects.filter(
                            subject__studentsubject__student=student,
                            deleted=False
                        ).order_by('start_datetime').annotate(day=Trunc('start_datetime', 'day'))
                        if start_timestamp:
                            occ = occ.filter(
                                start_datetime__gte=datetime.fromtimestamp(
                                    int(start_timestamp),
                                    tz=timezone(settings.TIME_ZONE)
                                )
                            )
                        if end_timestamp:
                            occ = occ.filter(
                                end_datetime__lte=datetime.fromtimestamp(
                                    int(end_timestamp),
                                    tz=timezone(settings.TIME_ZONE)
                                )
                            )
                        for day in (occ[0].day + timedelta(n) for n in
                                    range((occ[len(occ) - 1].day - occ[0].day).days + 2)):
                            day_occupancies = occ.filter(start_datetime__day=day.day)
                            if len(day_occupancies) == 0:
                                continue
                            if nb_per_day != 0:
                                day_occupancies = day_occupancies[:nb_per_day]
                            occ_list = []
                            for o in day_occupancies:
                                event = {
                                    'id': o.id,
                                    'group_name': f'Groupe {o.group_number}',
                                    'subject_name': o.subject.name,
                                    'teacher_name': f'{o.teacher.first_name} {o.teacher.last_name}',
                                    'start': o.start_datetime.timestamp(),
                                    'end': o.end_datetime.timestamp(),
                                    'occupancy_type': o.occupancy_type,
                                    'name': o.name,
                                }
                                if o.subject:
                                    event['class_name'] = o.subject._class.name
                                if o.classroom:
                                    event['classroom_name'] = o.classroom.name
                                occ_list.append(event)
                            days.append({'date': day.strftime("%d-%m-%Y"), 'occupancies': occ_list})
                        return days

                    return RF_Response({'status': 'success', 'days': get_days()})
                except Student.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class StudentSubjectDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the list of all subjects that a student participates in.',
        operation_description='Note : only students whose id match the one in the URL should be able to access this '
                              'route.',
        responses={
            200: Response(
                description='Student subjects',
                schema=Schema(
                    title='StudentSubjects',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'subjects': Schema(
                            type=TYPE_ARRAY,
                            items=Schema(
                                type=TYPE_OBJECT,
                                properties={
                                    'id': Schema(type=TYPE_INTEGER, example=166),
                                    'name': Schema(type=TYPE_STRING, example='PPPE'),
                                    'class_name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUE'),
                                    'teachers': teacher_list_schema,
                                    'groups': Schema(
                                        type=TYPE_ARRAY,
                                        items=Schema(
                                            type=TYPE_OBJECT,
                                            properties={
                                                'name': Schema(type=TYPE_STRING, example='Groupe 1'),
                                                'count': Schema(type=TYPE_INTEGER, example=166),
                                                'is_student_group': Schema(type=TYPE_BOOLEAN, example=False),
                                            },
                                            required=['name', 'count', 'is_student_group', ]
                                        )
                                    ),
                                },
                                required=['id', 'name', 'class_name', 'teachers', 'groups', ]
                            ),
                        ),
                    },
                    required=['status', 'subjects', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InsufficientAuthorization', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidID', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Students', 'role-student', ]
    )
    def get(self, request, student_id):
        try:
            token = self._get_token(request)
            if not token.user.id != student_id:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                student = Student.objects.get(id=student_id)
                def get_subjects() -> list:
                    subject_list = []
                    student_subjects = StudentSubject.objects.filter(student=student)
                    for ss in student_subjects:
                        # TODO check this shit
                        def get_subject_teachers() -> list:
                            teachers = []
                            teacher_subjects = TeacherSubject.objects.filter(subject=ss.subject)
                            for t in teacher_subjects:
                                teachers.append(
                                    {
                                        'first_name': t.teacher.first_name,
                                        'last_name': t.teacher.last_name,
                                        'in_charge': t.in_charge,
                                        'email': t.teacher.email,
                                        'phone_number': t.teacher.phone_number,
                                    }
                                )
                            return teachers

                        def get_subject_groups() -> list:
                            groups = []
                            for i in range(1, ss.subject.group_count + 1):
                                groups.append(
                                    {
                                        'name': f'Groupe {i}',
                                        'count': 0,
                                        'is_student_group': i == ss.group_number
                                    }
                                )
                            return groups

                        subject_list.append(
                            {
                                'id': ss.subject.id,
                                'name': ss.subject.name,
                                'class_name': ss.subject._class.name,
                                'teachers': get_subject_teachers(),
                                'groups': get_subject_groups(),
                            }
                        )
                    return subject_list

                return RF_Response({'status': 'success', 'subjects': get_subjects(), })
            except Student.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)
