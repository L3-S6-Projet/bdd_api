from datetime import datetime, timedelta

from django.conf import settings
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
from scolendar.exceptions import TeacherInChargeError
from scolendar.models import Student, Teacher, occupancy_list, Classroom, Class, Subject, \
    TeacherSubject, Occupancy
from scolendar.paginations import SubjectResultSetPagination
from scolendar.serializers import OccupancyCreationSerializer, SubjectSerializer, SubjectCreationSerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin
from scolendar.viewsets.common.schemas import occupancies_schema


class SubjectViewSet(GenericAPIView, TokenHandlerMixin):
    serializer_class = SubjectSerializer
    queryset = Subject.objects.all().order_by('id')
    pagination_class = SubjectResultSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('query', None)
        if query:
            if len(query) >= 3:
                queryset = queryset.filter(
                    Q(name__unaccent__icontains=query) |
                    Q(_class__name__unaccent_lower__trigram_similar=query)
                )
        return queryset

    @swagger_auto_schema(
        operation_summary='Returns a paginated list of all subjects.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              '10 subjects should be returned per page. At least three characters should be provided '
                              'for the search.',
        responses={
            200: Response(
                description='A list of all subjects.',
                schema=Schema(
                    title='SubjectListResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'total': Schema(
                            type=TYPE_INTEGER,
                            description='Total number of subjects',
                            example=166
                        ),
                        'subjects': Schema(
                            type=TYPE_ARRAY,
                            items=Schema(
                                type=TYPE_OBJECT,
                                properties={
                                    'id': Schema(type=TYPE_INTEGER, example=166),
                                    'class_name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUE'),
                                    'name': Schema(type=TYPE_STRING, example='PPPE'),
                                },
                                required=['class_name', 'name', ]
                            ),
                        ),
                    },
                    required=['status', 'total', 'subjects', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ],
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
                'subjects': response['results'],
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
        operation_summary='Creates a new subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            201: Response(
                description='Subject created',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
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
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid class id (code=`InvalidID`)\nInvalid teacher in charge id (code=`InvalidID`)',
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
                    }
                )
            ),
        },
        tags=['Subjects', ],
        request_body=Schema(
            title='SubjectCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='PPPE'),
                'class_id': Schema(type=TYPE_INTEGER, example=166),
                'teacher_in_charge_id': Schema(type=TYPE_INTEGER, example=166),
            },
            required=['name', 'class_id', 'teacher_in_charge_id', ]
        )
    )
    def post(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            try:
                serializer = SubjectCreationSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            except Class.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            return RF_Response(serializer.data, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Deletes the given students using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'This request should be denied if the subject is used in any occupancy (be it directly, '
                              'or via a group).',
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
            422: Response(
                description='Subject used in an occupancy (code=`SubjectUsed`)',
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
        tags=['Subjects', ],
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

            def delete_subject(student_id: int):
                subject = Subject.objects.get(id=student_id)
                subject.delete()

            for post_id in request.data:
                try:
                    delete_subject(post_id)
                except Subject.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets information on a subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Subject information',
                schema=Schema(
                    title='SubjectResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'subject': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                'name': Schema(type=TYPE_STRING, example='PPPE'),
                                'class_name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUEE'),
                                'total_hours': Schema(type=TYPE_INTEGER, example=166),
                                'teachers': Schema(
                                    type=TYPE_ARRAY,
                                    items=Schema(
                                        type=TYPE_OBJECT,
                                        properties={
                                            'id': Schema(type=TYPE_INTEGER, example=166),
                                            'first_name': Schema(type=TYPE_STRING, example='John'),
                                            'last_name': Schema(type=TYPE_STRING, example='Doe'),
                                            'in_charge': Schema(type=TYPE_BOOLEAN, example=False),
                                        },
                                        required=['id', 'first_name', 'last_name', 'in_charge', ]
                                    )
                                ),
                                'groups': Schema(
                                    type=TYPE_OBJECT,
                                    properties={
                                        'id': Schema(type=TYPE_INTEGER, example=166),
                                        'name': Schema(type=TYPE_STRING, example='Groupe 1'),
                                        'count': Schema(type=TYPE_INTEGER, example=166),
                                    },
                                    required=['id', 'name', 'count', ]
                                ),
                            },
                            required=[
                                'name',
                                'class_name',
                                'total_hours',
                                'teachers',
                                'groups',
                            ]
                        ),
                    },
                    required=['status', 'subject', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ]
    )
    def get(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                subject = Student.objects.get(id=subject_id)

                # TODO check this shit
                def get_subject_teachers() -> list:
                    teachers = []
                    teacher_subjects = TeacherSubject.objects.filter(subject=subject)
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
                    for i in range(1, subject.group_count + 1):
                        groups.append(
                            {
                                'name': f'Groupe {i}',
                                'count': 0,
                                'is_student_group': i == subject.group_number
                            }
                        )
                    return groups

                def count_hours() -> int:
                    total = 0
                    occupancies = Occupancy.objects.get(subject=subject)
                    for occ in occupancies:
                        total += occ.duration.seconds / 3600.
                    return total

                subject = {
                    'name': subject.name,
                    'class_name': subject._class.name,
                    'total_hours': count_hours(),
                    'teachers': get_subject_teachers(),
                    'groups': get_subject_groups()
                }
                return RF_Response({'status': 'success', 'subject': subject})
            except Student.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Updates information for a subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'The teacher designed by teacher_in_charge_id should already be a teacher of that '
                              'subject.',
        responses={
            200: Response(
                description='Subject updated',
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
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID (code=`InvalidID`)\nInvalid teacher in charge id (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='The provided teacher in charge is not already a teacher of the subject '
                            '(code=`TeacherNotInCharge`)',
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
        tags=['Subjects', ],
        request_body=Schema(
            title='SubjectUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='PPPE'),
                'class_id': Schema(type=TYPE_INTEGER, example=166),
                'teacher_in_charge_id': Schema(type=TYPE_INTEGER, example=166),
            },
            required=['name', 'class_id', 'teacher_in_charge_id', ]
        )
    )
    def put(self, request, student_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                subject = Subject.objects.get(id=student_id)
                data = request.data
                data_keys = data.keys()
                if 'name' in data_keys:
                    subject.name = data['first_name']
                if 'class_id' in data_keys:
                    try:
                        _class = Class.objects.get(id=data['class_id'])
                        subject._class = _class
                    except Class.DoesNotExist:
                        return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
                if 'teacher_in_charge_id' in data_keys:
                    try:
                        new_teacher_in_charge = Teacher.objects.get(id=data['teacher_in_charge_id'])
                        try:
                            subject_teacher = TeacherSubject.objects.get(subject_id=subject.id, in_charge=True)
                            subject_teacher.in_charge = False
                        except TeacherSubject.DoesNotExist:
                            pass
                        try:
                            subject_teacher = TeacherSubject.objects.get(teacher=new_teacher_in_charge, subject=subject)
                        except TeacherSubject.DoesNotExist:
                            subject_teacher = TeacherSubject(teacher=new_teacher_in_charge, subject=subject)
                        subject_teacher.in_charge = True
                        subject_teacher.save()
                    except Teacher.DoesNotExist:
                        return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
                subject.save()
                return RF_Response({'status': 'success'})
            except Student.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectOccupancyViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a subject for the given time period.',
        operation_description='Note : only users with the role `administrator`, or professors who are a teacher of the '
                              'subject should be able to access this route.',
        responses={
            200: Response(
                description='Subject occupancies',
                schema=occupancies_schema
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', 'role-professor', ],
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
    def get(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                student = Subject.objects.get(id=subject_id)

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

    @swagger_auto_schema(
        operation_summary='Creates a new occupancy for a given subject.',
        operation_description='Note : only professors who are a teacher of the subject should be able to access this'
                              ' route.\nThe occupancy types `td` and `tp` should be rejected. Only classrooms that are'
                              ' free should be accepted. Only classes that are not (any of their groups too) in any'
                              ' classes at the specified time should be accepted.',
        responses={
            201: Response(
                description='Data saved',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                    }
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
            404: Response(
                description='Invalid ID (code=`InvalidID`)\nInvalid classroom ID (code=`InvalidID`)\nInvalid teacher ID'
                            ' (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
            422: Response(
                description='Invalid occupancy type (code=`InvalidOccupancyType`)\nThe classroom is already occupied '
                            '(code=`ClassroomAlreadyOccupied`)\nThe class (or group) is already occupied '
                            '(code=`ClassOrGroupAlreadyOccupied`).\nEnd is before start (code=`EndBeforeStart`)\nThe '
                            'teacher does not teach that subject (code=`TeacherDoesNotTeach`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
        },
        tags=['role-professor', ],
        request_body=Schema(
            title='OccupancyCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'classroom_id': Schema(type=TYPE_INTEGER, example=166),
                'start': Schema(type=TYPE_INTEGER, example=166),
                'end': Schema(type=TYPE_INTEGER, example=166),
                'name': Schema(type=TYPE_STRING, example='Algorithmique CM Groupe 1'),
                'occupancy_type': Schema(type=TYPE_STRING, enum=occupancy_list),
                'teacher_id': Schema(type=TYPE_INTEGER, example=166),
            },
            required=['classroom_id', 'start', 'end', 'name', 'occupancy_type', 'teacher_id', ]
        )
    )
    def post(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            try:
                serializer = OccupancyCreationSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(subject_id)
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            except Subject.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            return RF_Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectTeacherViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Adds new teachers to a subject using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            201: Response(
                description='Teachers added',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ],
        request_body=Schema(
            title='IDRequest',
            type=TYPE_ARRAY,
            items=Schema(type=TYPE_INTEGER, example=166),
        )
    )
    def post(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            try:
                subject = Subject.objects.get(id=subject_id)
                for post_id in request.data:
                    subject_teacher = TeacherSubject(subject=subject, teacher_id=post_id)
                    subject_teacher.save()
            except Subject.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            return RF_Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Removes teachers from a subject using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'This request should be denied if there is less than one teacher in the subject, or if '
                              'the teacher is in charge.',
        responses={
            200: Response(
                description='Teachers removed',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Less than one teacher in charge (code=`LastTeacherInSubject`)\nThe teacher is in charge '
                            '(code=`TeacherInCharge`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ],
        request_body=Schema(
            title='IDRequest',
            type=TYPE_ARRAY,
            items=Schema(type=TYPE_INTEGER, example=166),
        )
    )
    def delete(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)

            def remove_teacher_from_subject(teacher_id: int):
                subject_teachers = TeacherSubject.objects.filter(subject_id=subject_id)
                if len(subject_teachers) <= 1:
                    raise TeacherInChargeError('Not enough teachers')

                subject_teacher = TeacherSubject.objects.get(teacher_id=teacher_id, subject_id=subject_id)
                if subject_teacher.in_charge:
                    raise TeacherInChargeError('Teacher is in charge')
                subject_teacher.delete()

            for post_id in request.data:
                try:
                    remove_teacher_from_subject(post_id)
                except TeacherSubject.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
                except TeacherInChargeError:
                    return RF_Response({'status': 'error', 'code': 'TeacherInCharge'},
                                       status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectGroupViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Adds a new group to a subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'This should trigger the re-organization of groups.',
        responses={
            201: Response(
                description='Groups added',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
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
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects']
    )
    def post(self, request, subject_id):
        # TODO check this shit
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.group_count += 1
                subject.save()
                return RF_Response({'status': 'success'})
            except Subject.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Removes a group from a subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'This should trigger the re-organisation of groups. This request should be denied if '
                              'there is less than one group in the subject.',
        responses={
            200: Response(
                description='Groups removed',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='This is the last group for this subject (code=`LastGroupInSubject`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects']
    )
    def delete(self, request, subject_id):
        # TODO check this shit
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            try:
                subject = Subject.objects.get(id=subject_id)
                if subject.group_count == 1:
                    return RF_Response({'status': 'error', 'code': 'LastGroupInSubject'})
                subject.group_count -= 1
                subject.save()
                return RF_Response({'status': 'success'})
            except Subject.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectGroupOccupancyViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a subject for the given time period.',
        operation_description='Note : only professors who are a teacher of the subject should be able to access this '
                              'route.',
        responses={
            200: Response(
                description='Groups occupancies',
                schema=occupancies_schema,
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['role-professor', ],
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
    def get(self, request, subject_id, group_number):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                subject = Subject.objects.get(id=subject_id)

                def get_days() -> list:
                    start_timestamp = request.query_params.get('start', None)
                    end_timestamp = request.query_params.get('end', None)
                    nb_per_day = int(request.query_params.get('occupancies_per_day', 0))
                    days = []
                    occ = Occupancy.objects.filter(
                        subject=subject,
                        group_number=group_number,
                        deleted=False,
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
            except Class.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Creates a new occupancy for a given group of a subject.',
        operation_description='Note : only professors who are a teacher of the subject should be able to access this '
                              'route.\nThe only accepted occupancy types should be `td` and `tp`.\nThe classroom id '
                              'should **NOT** be nullable. Only classrooms that are free should be accepted. Only '
                              'groups that are not (and their class too) in any classes at the specified time should '
                              'be accepted.',
        responses={
            200: Response(
                description='Data saved',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
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
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID (code=`InvalidID`)\nInvalid classroom ID (code=`InvalidID`)\nInvalid teacher ID'
                            ' (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid occupancy type (code=`InvalidOccupancyType`)\nThe classroom is already occupied '
                            '(code=`ClassroomAlreadyOccupied`)\nThe class (or group) is already occupied '
                            '(code=`ClassOrGroupAlreadyOccupied`).\nEnd is before start (code=`EndBeforeStart`)\nThe '
                            'teacher does not teach that subject (code=`TeacherDoesNotTeach`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['role-professor', ],
        request_body=Schema(
            title='OccupancyCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'classroom_id': Schema(type=TYPE_INTEGER, example=166),
                'start': Schema(type=TYPE_INTEGER, example=166),
                'end': Schema(type=TYPE_INTEGER, example=166),
                'name': Schema(type=TYPE_STRING, example='new_password'),
                'occupancy_type': Schema(type=TYPE_STRING, enum=occupancy_list),
                'teacher_id': Schema(type=TYPE_INTEGER, example=166)
            },
            required=['classroom_id', 'start', 'end', 'name', 'occupancy_type', 'teacher_id', ]
        )
    )
    def post(self, request, subject_id, group_number):
        # TODO check this shit
        try:
            token = self._get_token(request)
            try:
                Teacher.objects.get(id=token.user.id)
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                subject = Subject.objects.get(id=subject_id)
                data = request.data
                classroom = Classroom.objects.get(id=data.classroom_id)
                teacher = Teacher.objects.get(id=request.data.teacher_id)
                start_datetime = datetime.fromtimestamp(data.start)
                end_datetime = datetime.fromtimestamp(data.end)
                occupancy = Occupancy(
                    classroom=classroom,
                    group_number=group_number,
                    subject=subject,
                    teacher=teacher,
                    start_datetime=start_datetime,
                    duration=end_datetime - start_datetime,
                    occupancy_type=data.occupancy_type,
                    name=data.name
                )
                occupancy.save()
                return RF_Response({'status': 'success'})
            except Subject.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)
