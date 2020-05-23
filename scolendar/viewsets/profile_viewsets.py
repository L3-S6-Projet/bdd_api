from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_yasg.openapi import Schema, Response, TYPE_OBJECT, TYPE_STRING, TYPE_ARRAY, TYPE_INTEGER
from drf_yasg.utils import swagger_auto_schema
from pytz import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.models import occupancy_list, Student, OccupancyModification, ICalToken, Occupancy
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin


class ProfileViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Updates the user model.',
        operation_description='Should be accessible by every user.',
        responses={
            200: Response(
                description='Data updated',
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
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, example='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Invalid old_password (code=`InvalidOldPassword`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, example='InvalidOldPassword', enum=error_codes),
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
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, example='PasswordTooSimple', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Profile', 'role-student', 'role-professor', ],
        request_body=Schema(
            title='ProfileUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'old_password': Schema(type=TYPE_STRING, example='12345'),
                'new_password': Schema(type=TYPE_STRING, example='54321'),
            }, required=['old_password', 'new_password', ]
        )
    )
    def put(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            correct_old_password = token.user.check_password(request.data['old_password'])
            if not correct_old_password:
                return RF_Response({'status': 'error', 'code': 'InvalidOldPassword'}, status=status.HTTP_403_FORBIDDEN)
            user = User.objects.get(id=token.user.id)
            try:
                validate_password(request.data['new_password'])
                user.set_password(request.data['new_password'])
            except ValidationError:
                return RF_Response({'status': 'error', 'code': 'PasswordTooSimple'},
                                   status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ProfileLastOccupancyEdit(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Returns a list of all recent occupancies modifications that are relevant to the user.',
        operation_description='Modifications that are relevant are:\n- For a teacher: modifications of occupancies '
                              'about a subject that they teach, or modifications of their own external occupancies.\n- '
                              'For a student : modifications of occupancies about a subject that they take.\nOnly the '
                              'last 25 modifications should be returned.',
        responses={
            200: Response(
                description='Recent modifications',
                schema=Schema(
                    title='ProfileRecentModification',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'modifications': Schema(
                            type=TYPE_ARRAY,
                            items=Schema(
                                type=TYPE_OBJECT,
                                properties={
                                    'modification_type': Schema(
                                        type=TYPE_STRING,
                                        enum=['CREATION', 'EDIT', 'DELETION', ]
                                    ),
                                    'modification_timestamp': Schema(type=TYPE_INTEGER, example=1587987050),
                                    'occupancy': Schema(
                                        type=TYPE_OBJECT,
                                        properties={
                                            'subject_name': Schema(
                                                type=TYPE_STRING,
                                                example='PPPE (nullable if external)'
                                            ),
                                            'class_name': Schema(
                                                type=TYPE_STRING,
                                                example='L3 Informatique (nullable if external'
                                            ),
                                            'occupancy_type': Schema(type=TYPE_STRING, enum=occupancy_list),
                                            'occupancy_start': Schema(type=TYPE_INTEGER, example=1587987050),
                                            'occupancy_end': Schema(type=TYPE_INTEGER, example=1587987050),
                                            'previous_occupancy_start': Schema(
                                                description='Only for the edition modification_type',
                                                type=TYPE_INTEGER,
                                                example=1587987050,
                                            ),
                                            'previous_occupancy_end': Schema(
                                                description='Only for the edition modification_type',
                                                type=TYPE_INTEGER,
                                                example=1587987050
                                            ),
                                        },
                                        required=[
                                            'subject_name',
                                            'class_name',
                                            'occupancy_type',
                                            'occupancy_start',
                                            'occupancy_end',
                                        ]
                                    )
                                },
                                required=['modification_type', 'modification_timestamp', 'occupancy', ]
                            )
                        )
                    },
                    required=['status', 'modifications', ]
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
                    }
                )
            ),
            403: Response(
                description='Insufficient rights (administrator) (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
        },
        tags=['role-professor', 'role-student', ],
    )
    def get(self, request):
        try:
            token = self._get_token(request)
            if token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                student = Student.objects.get(id=token.user.id)
                occ_modifications = OccupancyModification.objects.filter(
                    occupancy__subject__studentsubject__student=student).order_by('-modification_date')[:25]
                modifications = []
                for occ in occ_modifications:
                    occupancy = {
                        'subject_name': occ.occupancy.subject.name if occ.occupancy.occupancy_type != 'EXT' else None,
                        'class_name': occ.occupancy.subject._class.name if occ.occupancy.occupancy_type != 'EXT' else None,
                        'occupancy_type': occ.occupancy.occupancy_type,
                        'occupancy_start': occ.new_start_datetime.timestamp(),
                        'occupancy_end': (occ.new_start_datetime + occ.new_duration).timestamp(),
                    }
                    if occ.modification_type == 'EDITION':
                        occupancy['previous_occupancy_start'] = occ.previous_start_datetime.timestamp()
                        occupancy['previous_occupancy_end'] = (
                                occ.previous_start_datetime + occ.previous_duration).timestamp()
                    modifications.append({
                        'modification_type': occ.modification_type,
                        'modification_timestamp': occ.modification_date.timestamp(),
                        'occupancy': occupancy
                    })
                return RF_Response({'status': 'success', 'modification': modifications})
            except Student.DoesNotExist:
                pass
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ProfileNextOccupancy(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the user\'s next occupancy',
        operation_description='',
        responses={
            200: Response(
                description='Success',
                schema=Schema(
                    title='',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'occupancy': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                'id': Schema(type=TYPE_INTEGER, example=166),
                                'classroom_name': Schema(type=TYPE_STRING, example='B.001'),
                                'group_name': Schema(type=TYPE_STRING, example='Groupe 1'),
                                'subject_name': Schema(type=TYPE_STRING, example='Algorithmique'),
                                'teacher_name': Schema(type=TYPE_STRING, example='John Doe'),
                                'start': Schema(type=TYPE_INTEGER, example=1587776227),
                                'end': Schema(type=TYPE_INTEGER, example=1587776227),
                                'occupancy_type': Schema(type=TYPE_STRING, enum=occupancy_list),
                                'class_name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUE'),
                                'name': Schema(type=TYPE_STRING, example='Algorithmique TP Groupe 1'),
                            },
                            required=[
                                'id',
                                'group_name',
                                'subject_name',
                                'teacher_name',
                                'start',
                                'end',
                                'occupancy_type',
                                'name',
                            ]
                        ),
                    },
                    required=['status', 'occupancy', ]
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
                description='Insufficient rights (administrator) (code=`InsufficientAuthorization`)',
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
        tags=['role-professor', 'role-student']
    )
    def get(self, request):
        try:
            token = self._get_token(request)
            if token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            o = Occupancy.objects.filter(start_datetime__gte=datetime.now(tz=timezone(settings.TIME_ZONE))).order_by(
                'start_datetime')[0]
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
            return RF_Response({'status': 'success', 'occupancy': event})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ProfileICalFeed(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the URL for the iCal feed for the user\'s calendar',
        operation_description='',
        responses={
            200: Response(
                description='Success',
                schema=Schema(
                    title='',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'url': Schema(type=TYPE_STRING, example='http://localhost:3030/api/feeds/ical/$TOKEN'),
                    },
                    required=['status', 'url', ]
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
                description='Insufficient rights (administrator) (code=`InsufficientAuthorization`)',
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
        tags=['role-professor', 'role-student']
    )
    def get(self, request):
        try:
            token = self._get_token(request)
            if token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            token, created = ICalToken.objects.get_or_create(user=token.user)
            return RF_Response({'status': 'success', 'url': f'{request.build_absolute_uri("/api/feeds/ical/")}{token}'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
