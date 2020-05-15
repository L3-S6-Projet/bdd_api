from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q
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

from scolendar.errors import error_codes
from scolendar.models import Classroom, levels, Class, Occupancy
from scolendar.paginations import ClassResultSetPagination
from scolendar.serializers import ClassSerializer, ClassCreationSerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin
from scolendar.viewsets.common.schemas import occupancies_schema


class ClassViewSet(GenericAPIView, TokenHandlerMixin):
    serializer_class = ClassSerializer
    queryset = Class.objects.all()
    pagination_class = ClassResultSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get('query', None)
        if query:
            if len(query) >= 3:
                queryset = queryset.filter(
                    Q(name__unaccent__icontains=query)
                )
        return queryset.order_by('id')

    @swagger_auto_schema(
        operation_summary='Returns a paginated list of all classes.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n10'
                              ' classes should be returned per page. At least three characters should be provided for '
                              'the search, or the results won\'t be filtered.',
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
                                title='ClassWithId',
                                type=TYPE_OBJECT,
                                properties={
                                    'id': Schema(type=TYPE_INTEGER, example=166),
                                    'name': Schema(type=TYPE_STRING, example='L3 Informatique'),
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
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except AttributeError:
            return RF_Response({'status': 'error', 'code': 'InvalidCredentials'},
                               status=status.HTTP_401_UNAUTHORIZED)
        except NotFound:
            data = {
                'status': 'success',
                'total': len(self.get_queryset()),
                'teachers': [],
            }
            return RF_Response(data)

    @swagger_auto_schema(
        operation_summary='Creates a new class.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
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
                description='Invalid level (code=`InvalidLevel`)',
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
        tags=['Classes'],
        request_body=Schema(
            title='ClassCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='L3 Informatique'),
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
        responses={
            200: Response(
                description='Data deleted',
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
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InvalidID',
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Class is still used by a subject (code=`ClassUsed`)\nA student is still in this class '
                            '(code=`StudentInClass`)',
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
                            title='Class',
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
                description='Insufficient rights (code=`InsufficientAuthorization`)',
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
                        'code': Schema(type=TYPE_STRING, value='InsufficientAuthorization', enum=error_codes),
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
                description='Invalid level (code=`InvalidLevel`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, example='InvalidLevel', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Classes', ],
        request_body=Schema(
            title='ClassUpdateRequest',
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
                schema=occupancies_schema
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
    def get(self, request, class_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                _class = Class.objects.get(id=class_id)

                def get_days() -> list:
                    start_timestamp = request.query_params.get('start', None)
                    end_timestamp = request.query_params.get('end', None)
                    nb_per_day = int(request.query_params.get('occupancies_per_day', 0))

                    days = []
                    occ = Occupancy.objects.filter(
                        subject___class=_class,
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
            except Class.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)
