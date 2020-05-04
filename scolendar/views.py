from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_ARRAY, TYPE_INTEGER, TYPE_STRING, \
    TYPE_BOOLEAN, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from conf.conf import get_service_coefficients
from scolendar.models import Student, Teacher, ranks, occupancy_list, Classroom
from scolendar.paginations import PaginationHandlerMixin, StudentResultSetPagination, ClassroomResultSetPagination
from scolendar.serializers import TeacherCreationSerializer, TeacherSerializer, ClassroomCreationSerializer, \
    ClassroomSerializer, StudentCreationSerializer, StudentSerializer
from scolendar.validators import phone_number_validator

error_codes = [
    'InvalidCredentials',
    'InsufficientAuthorization',
    'MalformedData',
    'InvalidOldPassword',
    'PasswordTooSimple',
    'InvalidEmail',
    'InvalidPhoneNumber',
    'InvalidRank',
    'InvalidID',
    'InvalidCapacity',
    'TeacherInCharge'
]

teacher_student_post_response = {
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
        description='Unauthorized access',
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
        description='Invalid ID(s)',
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
}


class TokenHandlerMixin:
    @staticmethod
    def _get_token(request):
        rec_token = request.META.get('HTTP_AUTHORIZATION')
        return Token.objects.get(key=rec_token)


class AuthViewSet(ObtainAuthToken, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Logins the user to the application, returning a new auth token and the user role.',
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
                description='Unauthorized access',
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
                elif Teacher.objects.get(id=user.id):
                    return 'TEA'
                elif Student.objects.get(id=user.id):
                    return 'STU'

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
            403: Response(
                description='Invalid credentials (code=`InvalidCredentials`)',
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


######################################################
#                                                    #
#                       Teacher                      #
#                                                    #
######################################################


class TeacherViewSet(APIView, PaginationHandlerMixin, TokenHandlerMixin):
    pagination_class = StudentResultSetPagination

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
                    }, required=['status', 'total', 'teachers', ])),
            401: Response(
                description='Unauthorized access',
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
                    }, required=['status', 'code', ])),
        },
        tags=['Teachers'],
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
            queryset = Teacher.objects.all()
            serializer = TeacherSerializer(queryset, many=True)
            data = {
                'status': 'success',
                'total': len(serializer.data),
                'teachers': serializer.data,
            }
            return RF_Response(data)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

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
                description='Unauthorized access',
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
                description='Insufficient rights (code=`InvalidCredentials`)',
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
                              'This request should trigger the re-organization of students in the affected groups.',
        responses=teacher_student_post_response,
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
                description='Insufficient rights (code=`InvalidCredentials`)',
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
                    # TODO finish this shit
                    return services

                service_list = get_services()

                def count_service_value() -> int:
                    coefficients = get_service_coefficients()
                    total = 0
                    for entry in service_list:
                        for k, v in coefficients:
                            total += entry[k] * float(v)
                    return total

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
                description='Insufficient rights (code=`InvalidCredentials`)',
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
                schema=Schema(
                    title='TeacherResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'occupancies': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                '05-01-2020': Schema(
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
                                )
                            },
                            required=[
                                'status',
                                'occupancies',
                            ]
                        ),
                    },
                    required=['status', 'occupancies', ]
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
                description='Insufficient rights (code=`InvalidCredentials`)',
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

                def get_occupancies() -> dict:
                    occupancies = {}
                    # TODO finish this other shit
                    return occupancies

                response = {
                    'status': 'success',
                    'occupancies': get_occupancies(),
                }
                return RF_Response(response)
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
                                    'teachers': Schema(
                                        type=TYPE_ARRAY,
                                        items=Schema(
                                            type=TYPE_OBJECT,
                                            properties={
                                                'first_name': Schema(type=TYPE_STRING, example='John'),
                                                'last_name': Schema(type=TYPE_STRING, example='Doe'),
                                                'in_charge': Schema(type=TYPE_BOOLEAN, example=True),
                                                'email': Schema(type=TYPE_STRING, example='cranky.duck@example.com'),
                                                'phone_number': Schema(type=TYPE_STRING, example='06 61 66 16 61'),
                                            },
                                            required=['first_name', 'last_name', 'in_charge', 'email', 'phone_number', ]
                                        )
                                    ),
                                    'groups': Schema(
                                        type=TYPE_ARRAY,
                                        items=Schema(
                                            type=TYPE_OBJECT,
                                            properties={
                                                'id': Schema(type=TYPE_INTEGER, example=166),
                                                'name': Schema(type=TYPE_STRING, example='Groupe 1'),
                                                'count': Schema(type=TYPE_INTEGER, example=166),
                                            },
                                            required=['id', 'name', 'count', ]
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
                description='Insufficient rights (code=`InvalidCredentials`)',
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
                    subjects = []
                    # TODO finish yet another shit
                    return subjects

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


########################################################
#                                                      #
#                       Classroom                      #
#                                                      #
########################################################


class ClassroomViewSet(APIView, PaginationHandlerMixin, TokenHandlerMixin):
    pagination_class = ClassroomResultSetPagination

    @swagger_auto_schema(
        operation_summary='Returns a paginated list of all classrooms.',
        operation_description='Note : only users with the role `administrator`, or professors, should be able to access'
                              ' this route.\n10 classrooms should be returned per page. If less than three characters'
                              ' are provided for the query, it will not be applied.',
        responses={
            200: Response(
                description='A list of all classrooms.',
                schema=Schema(
                    title='ClassroomList',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING,
                                         example='success'),
                        'total': Schema(type=TYPE_INTEGER,
                                        description='Total number of classrooms',
                                        example=166),
                        'classrooms': Schema(type=TYPE_ARRAY,
                                             items=Schema(
                                                 type=TYPE_OBJECT,
                                                 properties={
                                                     'id': Schema(
                                                         type=TYPE_INTEGER,
                                                         example=166),
                                                     'name': Schema(
                                                         type=TYPE_STRING,
                                                         example='John'),
                                                     'capacity': Schema(
                                                         type=TYPE_INTEGER,
                                                         example=166),
                                                 }, required=['id', 'name', 'capacity', ]), ),
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
                            value='InsufficientAuthorization',
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
        },
        tags=['Classroom'],
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
            queryset = Classroom.objects.all()
            serializer = ClassroomSerializer(queryset, many=True)
            data = {
                'status': 'success',
                'total': len(serializer.data),
                'teachers': serializer.data,
            }
            return RF_Response(data)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Creates a new classroom.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            201: Response(
                description='Classroom created',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING,
                                         example='success'),
                    }, required=['status', ])),
            401: Response(
                description='Unauthorized access',
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
                description='Insufficient rights (code=`InvalidCredentials`)',
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
        tags=['Classroom'],
        request_body=Schema(
            title='ClassroomCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='John'),
                'capacity': Schema(type=TYPE_INTEGER, example=166),
            }, required=['name', 'capacity', ]
        )
    )
    def post(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            serializer = ClassroomCreationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return RF_Response(serializer.data, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Deletes the given classrooms using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'This request should be denied if the classroom is used in any occupancy.',
        responses=teacher_student_post_response,
        tags=['Classroom'],
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

            def delete_classroom(classroom_id: int):
                classroom = Classroom.objects.get(id=classroom_id)
                classroom.delete()

            for post_id in request.data:
                try:
                    delete_classroom(post_id)
                except Classroom.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)

            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ClassroomDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets information for a classroom.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Teacher information',
                schema=Schema(
                    title='TeacherResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'classroom': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                'id': Schema(type=TYPE_INTEGER, example=166),
                                'name': Schema(type=TYPE_STRING, example='B.001'),
                                'capacity': Schema(type=TYPE_STRING, example=166),
                            },
                            required=[
                                'id',
                                'name',
                                'capacity',
                            ]
                        ),
                    },
                    required=['status', 'classroom', ]
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
                description='Insufficient rights (code=`InvalidCredentials`)',
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
        tags=['Classroom', ]
    )
    def get(self, request, classroom_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                classroom = Classroom.objects.get(id=classroom_id)

                classroom = {
                    'id': classroom.id,
                    'name': classroom.name,
                    'capacity': classroom.capacity,
                }
                return RF_Response({'status': 'success', 'classroom': classroom})
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Updates information for a classroom.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'The omission of the `capacity` field is not an error : it should not be able to be '
                              'modified.',
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
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, example='PasswordTooSimple', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Classroom', ],
        request_body=Schema(
            title='ClassroomUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='B.001'),
            },
            required=['name', ]
        )
    )
    def put(self, request, classroom_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                classroom = Classroom.objects.get(id=classroom_id)
                classroom.name = request.data['name']

                return RF_Response({'status': 'success', })
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ClassroomOccupancyViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a classroom for the given time period.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Classroom occupancies',
                schema=Schema(
                    title='Occupancies',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'occuupancies': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                '05-01-2020': Schema(
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
                                        'name': Schema(type=TYPE_STRING, example='Algorithmique CM Groupe 1'),
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
                            required=[
                                'id',
                                'name',
                                'capacity',
                            ]
                        ),
                    },
                    required=['status', 'occuupancies', ]
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
                description='Insufficient rights (code=`InvalidCredentials`)',
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
        tags=['Classroom', ],
        manual_parameters=[
            Parameter(name='start', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='end', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='occupancies_per_day', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
        ],
    )
    def get(self, request, classroom_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                classroom = Classroom.objects.get(id=classroom_id)

                def get_occupancies() -> dict:
                    occupancies = {}
                    # TODO some more shit to do
                    return occupancies

                return RF_Response({'status': 'success', 'occupancies': get_occupancies()})
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


######################################################
#                                                    #
#                       Student                      #
#                                                    #
######################################################


class StudentViewSet(APIView, PaginationHandlerMixin, TokenHandlerMixin):
    pagination_class = StudentResultSetPagination

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
                    }, required=['status', 'total', 'students', ])),
            401: Response(
                description='Unauthorized access',
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
                    }, required=['status', 'code', ])),
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
            queryset = Student.objects.all()
            serializer = StudentSerializer(queryset, many=True)
            data = {
                'status': 'success',
                'total': len(serializer.data),
                'students': serializer.data,
            }
            return RF_Response(data)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Creates a new student.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
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
                    }, required=['status', 'username', 'password', ])),
            401: Response(
                description='Unauthorized access',
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
                description='Insufficient rights (code=`InvalidCredentials`)',
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
        responses=teacher_student_post_response,
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
