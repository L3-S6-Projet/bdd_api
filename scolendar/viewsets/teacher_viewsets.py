from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models.functions import Trunc
from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_ARRAY, TYPE_INTEGER, TYPE_STRING, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from pytz import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from conf.conf import get_service_coefficients
from scolendar.errors import error_codes
from scolendar.models import Teacher, ranks, Occupancy, TeacherSubject
from scolendar.paginations import TeacherResultSetPagination
from scolendar.serializers import TeacherCreationSerializer, TeacherSerializer
from scolendar.validators import phone_number_validator
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin
from scolendar.viewsets.common.schemas import teacher_list_schema, occupancies_schema

occupancy_types = {
    'CM': 'cm',
    'TD': 'td',
    'TP': 'tp',
    'PROJ': 'projet',
    'ADM': 'administration',
    'EXT': 'external',
}


class TeacherViewSet(GenericAPIView, TokenHandlerMixin):
    serializer_class = TeacherSerializer
    queryset = Teacher.objects.all().order_by('id')
    pagination_class = TeacherResultSetPagination

    @swagger_auto_schema(
        operation_summary='Returns a paginated list of all teachers.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n10'
                              ' teachers should be returned per page. If less than three characters are provided '
                              'for the query, it will not be applied.\nWarning: the `email` and `phone_number` can be '
                              'null.',
        responses={
            200: Response(
                description='A list of all teachers.',
                schema=Schema(
                    title='TeacherListResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING,
                                         example='success'),
                        'total': Schema(type=TYPE_INTEGER,
                                        description='Total number of students',
                                        example=166),
                        'teachers': Schema(type=TYPE_ARRAY,
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
                                                   'email': Schema(
                                                       type=TYPE_STRING,
                                                       example='john.doe@example.com'),
                                                   'phone_number': Schema(
                                                       type=TYPE_STRING,
                                                       example='06 61 66 16 61'
                                                   )
                                               }, required=['id', 'first_name', 'last_name', 'email',
                                                            'phone_number', ]), ),
                    },
                    required=['status', 'total', 'teachers', ]
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
        tags=['Teachers', ],
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
                'teachers': response['results'],
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
        operation_summary='Creates a new teacher.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              '`email` and `phone_number` can be null in the request.',
        responses={
            201: Response(
                description='Teacher created',
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
                    }, required=['status', 'username', 'password', ])),
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
                    }, required=['status', 'code', ]
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
                            value='InvalidCredentials',
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid email (code=`InvalidEmail`)\nInvalid phone number (code=`InvalidPhoneNumber`)\n'
                            'Invalid rank (code=`InvalidRank`)',
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
        tags=['Teachers'],
        request_body=Schema(
            title='StudentCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'first_name': Schema(type=TYPE_STRING, example='John'),
                'last_name': Schema(type=TYPE_STRING, example='Doe'),
                'email': Schema(type=TYPE_STRING, example='john.doe@email.com'),
                'phone_number': Schema(type=TYPE_STRING, example='06 61 66 16 61'),
                'rank': Schema(type=TYPE_STRING, enum=ranks),
            }, required=['first_name', 'last_name', 'email', 'phone_number', 'rank', ]
        )
    )
    def post(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            serializer = TeacherCreationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return RF_Response(serializer.data, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Deletes the given students using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'This request should be denied if the professors are in charge of any subjects. This '
                              'should cascade and delete any occupancies they are a part of, and remove them from any '
                              'subjects they took part in.',
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
            422: Response(
                description='The teacher is still in charge of a subject (code=`TeacherInCharge`).',
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
        tags=['Teachers'],
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

            def delete_teacher(student_id: int):
                student = Teacher.objects.get(id=student_id)
                student.delete()

            for post_id in request.data:
                try:
                    delete_teacher(post_id)
                except Teacher.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)

            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class TeacherDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets information for a teacher.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'Warning: the `email` and `phone_number` can be null.',
        responses={
            200: Response(
                description='Teacher information',
                schema=Schema(
                    title='TeacherResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'teacher': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                'first_name': Schema(type=TYPE_STRING, example='John'),
                                'last_name': Schema(type=TYPE_STRING, example='Doe'),
                                'username': Schema(type=TYPE_STRING, example='road_buddy'),
                                'email': Schema(type=TYPE_STRING, example='email@example.com'),
                                'phone_number': Schema(type=TYPE_STRING, example='06 61 66 16 61'),
                                'rank': Schema(type=TYPE_STRING, enum=ranks),
                                'total_services': Schema(type=TYPE_INTEGER, example=166),
                                'services': Schema(
                                    type=TYPE_ARRAY,
                                    items=Schema(
                                        type=TYPE_OBJECT,
                                        properties={
                                            'class': Schema(type=TYPE_STRING, example='L3 INFORMATIQUE'),
                                            'cm': Schema(type=TYPE_INTEGER, example=166),
                                            'projet': Schema(type=TYPE_INTEGER, example=166),
                                            'td': Schema(type=TYPE_INTEGER, example=166),
                                            'tp': Schema(type=TYPE_INTEGER, example=166),
                                            'administration': Schema(type=TYPE_INTEGER, example=166),
                                            'external': Schema(type=TYPE_INTEGER, example=166),
                                        },
                                        required=[
                                            'class',
                                            'cm',
                                            'projet',
                                            'td',
                                            'tp',
                                            'administration',
                                            'external',
                                        ]
                                    )
                                )
                            },
                            required=[
                                'first_name',
                                'last_name',
                                'username',
                                'email',
                                'phone_number',
                                'rank',
                                'total_services',
                                'services',
                            ]
                        ),
                    },
                    required=['status', 'teacher', ]
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
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
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
        tags=['Teachers', ]
    )
    def get(self, request, teacher_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                teacher = Teacher.objects.get(id=teacher_id)

                def get_services() -> list:
                    services = []
                    # TODO check this shit
                    teacher_subjects = TeacherSubject.objects.filter(teacher=teacher)
                    for ts in teacher_subjects:
                        service_entry = {'class': teacher_subjects.subject._class.name}
                        for s_type in service_list:
                            try:
                                occupancies = Occupancy.objects.get(teacher=teacher, occupancy_type=s_type,
                                                                    subject=ts.subject)
                            except Occupancy.DoesNotExist:
                                service_entry[occupancy_types[s_type]] = 0
                                continue
                            total = 0
                            for occ in occupancies:
                                total += occ.duration / 3600.
                            service_entry[occupancy_types[s_type]] = total
                    return services

                service_list = get_services()

                def count_service_value() -> int:
                    coefficients = get_service_coefficients()
                    total = 0
                    for entry in service_list:
                        for k, v in coefficients:
                            total += entry[occupancy_types[k]] * float(v)
                    return total

                try:
                    teacher = {
                        'first_name': teacher.first_name,
                        'last_name': teacher.last_name,
                        'username': teacher.username,
                        'email': teacher.email,
                        'phone_number': teacher.phone_number,
                        'rank': teacher.rank,
                        'total_services': count_service_value(),
                        'services': service_list,
                    }
                except TeacherSubject.DoesNotExist:
                    teacher = {
                        'first_name': teacher.first_name,
                        'last_name': teacher.last_name,
                        'username': teacher.username,
                        'email': teacher.email,
                        'phone_number': teacher.phone_number,
                        'rank': teacher.rank,
                        'total_services': 0,
                        'services': [],
                    }
                return RF_Response({'status': 'success', 'teacher': teacher})
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Updates information for a teacher.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'Only filled fields should be updated. To remove the `phone_number` or `email` fields, '
                              'pass `null`.',
        responses={
            200: Response(
                description='Teacher updated',
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
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
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
                        'code': Schema(type=TYPE_STRING, value='InsufficientAuthorization', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid email (code=`InvalidEmail`)\nInvalid phone number (code=`InvalidPhoneNumber`)\n'
                            'Invalid rank (code=`InvalidRank`)\nPassword too simple (code=`PasswordTooSimple`)',
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
        tags=['Teachers', ],
        request_body=Schema(
            title='TeacherUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'first_name': Schema(type=TYPE_STRING, example='John'),
                'last_name': Schema(type=TYPE_STRING, example='Doe'),
                'email': Schema(type=TYPE_STRING, example='mail@eaxmple.com'),
                'phone_number': Schema(type=TYPE_STRING, example='06 61 66 16 61'),
                'rank': Schema(type=TYPE_STRING, enum=ranks),
                'password': Schema(type=TYPE_STRING, example='new_password'),
            }
        )
    )
    def put(self, request, teacher_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                data = request.data
                data_keys = data.keys()
                if 'first_name' in data_keys:
                    teacher.first_name = data['first_name']
                if 'last_name' in data_keys:
                    teacher.last_name = data['last_name']
                if 'email' in data_keys:
                    try:
                        validate_email(data['email'])
                        teacher.email = data['email']
                    except ValidationError:
                        return RF_Response({'status': 'error', 'code': 'InvalidEmail'},
                                           status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                if 'phone_number' in data_keys:
                    try:
                        phone_number_validator(data['phone_number'])
                        teacher.phone_number = data['phone_number']
                    except ValidationError:
                        return RF_Response({'status': 'error', 'code': 'InvalidPhoneNumber'},
                                           status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                if 'rank' in data_keys:
                    if data['rank'] not in ranks:
                        return RF_Response({'status': 'error', 'code': 'InvalidRank'},
                                           status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                    teacher.rank = data['rank']
                if 'password' in data_keys:
                    try:
                        validate_password(data['new_password'])
                        teacher.set_password(data['new_password'])
                    except ValidationError:
                        return RF_Response({'status': 'error', 'code': 'PasswordTooSimple'},
                                           status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                teacher.save()
                return RF_Response({'status': 'success'})
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class TeacherOccupancyDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a teacher for the given time period.',
        operation_description='Note : only users with the role `administrator`, or teachers whose id match the one in '
                              'the URL should be able to access this route.',
        responses={
            200: Response(
                description='Teacher information',
                schema=occupancies_schema,
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
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
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
        tags=['Teachers', 'role-professor', ],
        manual_parameters=[
            Parameter(name='start', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='end', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='occupancies_per_day', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
        ]
    )
    def get(self, request, teacher_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                teacher = Teacher.objects.get(id=teacher_id)

                def get_days() -> list:
                    start_timestamp = request.GET.get('start', None)
                    end_timestamp = request.GET.get('end', None)
                    nb_per_day = int(request.GET.get('occupancies_per_day', 0))

                    days = []
                    occ = Occupancy.objects.filter(
                        teacher=teacher,
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
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class TeacherSubjectDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the list of all subjects that a teacher participates in.',
        operation_description='Note : only teachers whose id match the one in the URL should be able to access this '
                              'route.',
        responses={
            200: Response(
                description='Teacher information',
                schema=Schema(
                    title='TeacherSubjects',
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
                                                'number': Schema(type=TYPE_INTEGER, example=166),
                                                'name': Schema(type=TYPE_STRING, example='Groupe 1'),
                                                'count': Schema(type=TYPE_INTEGER, example=166),
                                            },
                                            required=['number', 'name', 'count', ]
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
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
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
        tags=['Teachers', 'role-professor', ]
    )
    def get(self, request, teacher_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                teacher = Teacher.objects.get(id=teacher_id)

                def get_subjects() -> list:
                    subject_list = []
                    student_subjects = TeacherSubject.objects.filter(teacher=teacher)
                    # TODO check this shit
                    for ss in student_subjects:
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
                                        'number': i,
                                        'name': f'Groupe {i}',
                                        'count': 0,
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

                response = {
                    'status': 'success',
                    'subjects': get_subjects(),
                }
                return RF_Response(response)
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)
