from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_INTEGER, TYPE_STRING, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.models import Student, occupancy_list, Classroom, Class, Occupancy
from scolendar.serializers import OccupancySerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin
from scolendar.viewsets.responses_viewsets import delete_response


class OccupancyViewSet(APIView, TokenHandlerMixin):

    @swagger_auto_schema(
        operation_summary='Gets all the occupancies for the given time period.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Subject occupancies.',
                schema=Schema(
                    title='OccupancyListResponse',
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
                        ),
                    },
                    required=['status', 'occupancies', ]
                ),
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
        },
        tags=['Occupancies', ],
        manual_parameters=[
            Parameter(name='start', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='end', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='occupancies_per_day', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
        ],
    )
    def get(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            queryset = Occupancy.objects.all()
            serializer = OccupancySerializer(queryset, many=True)
            data = {
                'status': 'success',
                'occupancies': serializer.data,
            }
            return RF_Response(data)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class OccupancyDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets information for an occupancy.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Occupancy information',
                schema=Schema(
                    title='OccupancyResponse',
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
        tags=['Occupancies', ]
    )
    def get(self, request, occupancy_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                occupancy_obj = Occupancy.objects.get(id=occupancy_id)

                occupancy = {
                    'id': occupancy_obj.id,
                    'classroom_name': occupancy_obj.classroom.name,
                    'group_name': occupancy_obj.group.name,
                    'subject_name': occupancy_obj.subject.name,
                    'teacher_name': f'{occupancy_obj.teacher.first_name} {occupancy_obj.teacher.last_name}',
                    'start': occupancy_obj.start,
                    'end': occupancy_obj.start + occupancy_list.duration,
                    'occupancy_type': occupancy_obj.occupancy_type,
                    'class_name': occupancy_obj.subject._class.name,
                    'name': occupancy_obj.name,
                }
                return RF_Response({'status': 'success', 'occupancy': occupancy})
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
        tags=['Occupancies', 'role-professor', ],
        request_body=Schema(
            title='OccupancyUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'classroom_id': Schema(type=TYPE_INTEGER, example=166),
                'start': Schema(type=TYPE_INTEGER, example=166),
                'end': Schema(type=TYPE_INTEGER, example=166),
                'name': Schema(type=TYPE_STRING, example='new_password'),
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
                occupancy = Occupancy.objects.get(id=student_id)
                data = request.data
                data_keys = data.keys()
                if 'classroom_id' in data_keys:
                    try:
                        classroom = Classroom.objects.get(id=data['classroom_id'])
                        occupancy._class = classroom
                    except Class.DoesNotExist:
                        return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
                if 'start' in data_keys:
                    occupancy.last_name = data['start']
                if 'end' in data_keys:
                    occupancy.duration = data['end'] - occupancy.start_datetime
                if 'name' in data_keys:
                    occupancy.name = data['name']
                occupancy.save()
                return RF_Response({'status': 'success'})
            except Occupancy.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Deletes the given occupancies using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses=delete_response,
        tags=['Occupancies', 'role-professor', ],
    )
    def delete(self, request, occupancy_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)

            try:
                occupancy = Occupancy.objects.get(id=occupancy_id)
                occupancy.delete()

                return RF_Response({'status': 'success'})
            except Occupancy.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)
