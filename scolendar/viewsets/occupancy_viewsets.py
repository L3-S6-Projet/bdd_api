from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_INTEGER, TYPE_STRING, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.models import Classroom, Class, Occupancy
from scolendar.serializers import OccupancySerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin
from scolendar.viewsets.common.schemas import occupancies_schema


class OccupancyViewSet(APIView, TokenHandlerMixin):

    @swagger_auto_schema(
        operation_summary='Gets all the occupancies for the given time period.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Subject occupancies.',
                schema=occupancies_schema,
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
        tags=['Occupancies', ],
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
                description='Invalid ID (code=`InvalidID`)\nInvalid classroom ID (code=`InvalidID`)',
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
                description='The classroom is already occupied (code=`ClassroomAlreadyOccupied`)\nThe class (or group) '
                            'is already occupied (code=`ClassOrGroupAlreadyOccupied`).\nEnd is before start '
                            '(code=`EndBeforeStart`)',
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
        operation_description='Note : only `administrators` and professors who are a teacher of the subject should be '
                              'able to access this route.',
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
