from django.contrib.auth import authenticate, login, logout
from drf_yasg.openapi import Schema, Response, TYPE_OBJECT, TYPE_INTEGER, TYPE_STRING
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response as RF_Response

from scolendar.errors import error_codes
from scolendar.models import Student, Teacher


class TokenHandlerMixin:
    """
    Removes code duplication related to getting the token from the HTTP Header and parsing it.

    If a token is received, return the model instance of that token.
    """

    @staticmethod
    def _get_token(request):
        received = request.META.get('HTTP_AUTHORIZATION')
        if received is None:
            raise Token.DoesNotExist
        data = received.split(' ')
        if data[0] != 'Bearer':
            raise AttributeError('Token error')
        rec_token = data[-1]
        return Token.objects.get(key=rec_token)


class AuthViewSet(ObtainAuthToken, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Logs in the user to the application, returning a new auth token and the user role.',
        operation_description='',
        responses={
            201: Response(
                description='Valid credentials',
                schema=Schema(
                    title='SuccessfulLoginResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'token': Schema(type=TYPE_STRING, example='...'),
                        'user': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                'id': Schema(type=TYPE_INTEGER, example=166),
                                'first_name': Schema(type=TYPE_STRING),
                                'last_name': Schema(type=TYPE_STRING),
                                'kind': Schema(type=TYPE_STRING, enum=['ADM', 'STU', 'TEA', ])
                            },
                            required=['id', 'first_name', 'last_name', 'kind', ]
                        )
                    }, required=['status', 'token', 'user', ])),
            403: Response(
                description='Invalid credentials (code=`InsufficientAuthorization`)',
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
                    }, required=['status', 'code', ])),
        },
        tags=['Auth', 'role-student', 'role-professor', ],
        request_body=Schema(
            title='LoginRequest',
            type=TYPE_OBJECT,
            properties={
                'username': Schema(type=TYPE_STRING, example='azure_diamond'),
                'password': Schema(type=TYPE_STRING, example='hunter2'),
            },
            required=['username', 'password', ]
        )
    )
    def post(self, request, *args, **kwargs):
        user = authenticate(request, username=request.data['username'], password=request.data['password'])
        if user is not None:
            def get_user_type():
                if user.is_staff:
                    return 'ADM'
                try:
                    Teacher.objects.get(id=user.id)
                    return 'TEA'
                except Teacher.DoesNotExist:
                    pass
                try:
                    Student.objects.get(id=user.id)
                    return 'STU'
                except Student.DoesNotExist:
                    pass

            token, created = Token.objects.get_or_create(user=user)
            response = {
                'status': 'success',
                'token': token.key,
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'kind': get_user_type(),
                },
            }
            login(request, user)
            return RF_Response(response, status=status.HTTP_201_CREATED)
        else:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'}, status=status.HTTP_403_FORBIDDEN)

    @swagger_auto_schema(
        operation_summary='Destroys the given auth token.',
        operation_description='',
        responses={
            200: Response(
                description='Valid token',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success')
                    },
                    required=['status']
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
                    required=['status', 'code']
                )
            )
        },
        tags=['Auth', 'role-student', 'role-professor', ],
    )
    def delete(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if token.user:
                token.delete()
                logout(request)
                return RF_Response({'status': 'success'})
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'}, status=status.HTTP_403_FORBIDDEN)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'}, status=status.HTTP_403_FORBIDDEN)
