from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from drf_yasg.openapi import Schema, Response, TYPE_OBJECT, TYPE_STRING, TYPE_ARRAY, TYPE_INTEGER
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.models import occupancy_list
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
                        'status': Schema(type=TYPE_STRING, example='error'),
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
                                            'occupancy_ent': Schema(type=TYPE_INTEGER, example=1587987050),
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
                                        required=[]
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
        pass


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
        pass
