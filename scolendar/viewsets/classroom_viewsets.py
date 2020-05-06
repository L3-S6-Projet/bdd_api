from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_ARRAY, TYPE_INTEGER, TYPE_STRING, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.models import occupancy_list, Classroom
from scolendar.paginations import PaginationHandlerMixin, ClassroomResultSetPagination
from scolendar.serializers import ClassroomCreationSerializer, ClassroomSerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin
from scolendar.viewsets.responses_viewsets import update_response


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
        tags=['Classrooms'],
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
        tags=['Classrooms'],
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
        tags=['Classrooms'],
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
        tags=['Classrooms', ]
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
        responses=update_response,
        tags=['Classrooms', ],
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

                classroom.save()

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
        tags=['Classrooms', ],
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
