from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_ARRAY, TYPE_INTEGER, TYPE_STRING, \
    IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.models import occupancy_list, Classroom, levels, Class
from scolendar.paginations import PaginationHandlerMixin, ClassResultSetPagination
from scolendar.serializers import ClassSerializer, ClassCreationSerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin


class ClassViewSet(APIView, PaginationHandlerMixin, TokenHandlerMixin):
    pagination_class = ClassResultSetPagination

    class_responses = {
        201: Response(
            description='Class created',
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
    }

    @swagger_auto_schema(
        operation_summary='Returns a paginated list of all classes.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              '10 classes should be returned per page. At least three characters should be provided for'
                              ' the search.',
        responses={
            200: Response(
                description='A list of all classes.',
                schema=Schema(
                    title='ClassesList',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'total': Schema(type=TYPE_INTEGER, description='Total number of classes', example=166),
                        'classes': Schema(
                            type=TYPE_ARRAY,
                            items=Schema(
                                type=TYPE_OBJECT,
                                properties={
                                    'id': Schema(type=TYPE_INTEGER, example=166),
                                    'name': Schema(type=TYPE_STRING, example='John'),
                                    'level': Schema(type=TYPE_STRING, enum=levels),
                                },
                                required=['id', 'name', 'level', ]
                            ),
                        ),
                    },
                    required=['status', 'total', 'classes', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, value='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InsufficientAuthorization`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, value='error'),
                        'code': Schema(type=TYPE_STRING, value='InsufficientAuthorization', enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
        },
        tags=['Classes'],
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
            queryset = Class.objects.all()
            serializer = ClassSerializer(queryset, many=True)
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
        operation_summary='Creates a new class.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses=class_responses,
        tags=['Classes'],
        request_body=Schema(
            title='ClassCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='John'),
                'level': Schema(type=TYPE_STRING, enum=levels),
            }, required=['name', 'level', ]
        )
    )
    def post(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            serializer = ClassCreationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return RF_Response(serializer.data, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Deletes the given classes using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'This request should be denied if the class is used in any subject, or if any student is'
                              ' in this class.',
        responses=class_responses,
        tags=['Classes'],
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

            def delete_class(class_id: int):
                _class = Class.objects.get(id=class_id)
                _class.delete()

            for post_id in request.data:
                try:
                    delete_class(post_id)
                except Class.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)

            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ClassDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets information for a class.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Class information',
                schema=Schema(
                    title='ClassResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'class': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                'name': Schema(type=TYPE_STRING, example='B.001'),
                                'level': Schema(type=TYPE_STRING, enum=levels),
                            },
                            required=[
                                'name',
                                'level',
                            ]
                        ),
                        'total_services': Schema(type=TYPE_INTEGER, example=166),
                    },
                    required=['status', 'class', 'total_services', ]
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
        tags=['Classes', ]
    )
    def get(self, request, class_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                _class = Class.objects.get(id=class_id)

                _class = {
                    'name': _class.name,
                    'capacity': _class.level,
                }
                return RF_Response({'status': 'success', 'class': _class})
            except Class.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Updates information for a class.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
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
        tags=['Classes', ],
        request_body=Schema(
            title='ClassroomUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUE'),
                'level': Schema(type=TYPE_STRING, enum=levels),
            },
            required=['name', 'level', ]
        )
    )
    def put(self, request, classroom_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                _class = Class.objects.get(id=classroom_id)

                data_keys = request.data.keys()

                if 'name' in data_keys:
                    _class.name = request.data['name']
                if 'level' in data_keys:
                    _class.level = request.data['level']

                _class.save()

                return RF_Response({'status': 'success', })
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class ClassOccupancyViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a class for the given time period.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Class occupancies',
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
        tags=['Classes', ],
        manual_parameters=[
            Parameter(name='start', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='end', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='occupancies_per_day', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
        ],
    )
    def get(self, request, class_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                _class = Class.objects.get(id=class_id)

                def get_occupancies() -> dict:
                    occupancies = {}
                    # TODO even more shit to do
                    return occupancies

                return RF_Response({'status': 'success', 'occupancies': get_occupancies()})
            except Class.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)
