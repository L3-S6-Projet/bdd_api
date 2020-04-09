from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.utils import swagger_auto_schema
from inflection import camelize
from rest_framework import generics
from rest_framework.parsers import FileUploadParser, FormParser

from cal.models import Class, Rooms, Subject, Occupancy, TeacherOccupancy, ClassOccupancy
from cal.serializers import ClassSerializer, RoomSerializer, SubjectSerializer, OccupancySerializer, \
    ClassOccupancySerializer, TeacherOccupancySerializer


class CamelCaseOperationIDAutoSchema(SwaggerAutoSchema):
    def get_operation_id(self, operation_keys=None):
        operation_id = super(CamelCaseOperationIDAutoSchema, self).get_operation_id(operation_keys)
        return camelize(operation_id, uppercase_first_letter=False)


class ClassList(generics.ListCreateAPIView):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

    parser_classes = (FormParser, CamelCaseJSONParser, FileUploadParser)
    renderer_classes = (CamelCaseJSONRenderer,)
    swagger_schema = CamelCaseOperationIDAutoSchema

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        """post method docstring"""
        return super(ClassList, self).post(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='class_delete_bulk',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'body': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='this should not crash (request body on DELETE method)'
                )
            }
        ),
    )
    def delete(self, *args, **kwargs):
        """summary from docstring
        description body is here, summary is not included
        """
        pass


class RoomList(generics.ListCreateAPIView):
    queryset = Rooms.objects.all()
    serializer_class = RoomSerializer

    parser_classes = (FormParser, CamelCaseJSONParser, FileUploadParser)
    renderer_classes = (CamelCaseJSONRenderer,)
    swagger_schema = CamelCaseOperationIDAutoSchema

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        """post method docstring"""
        return super(RoomList, self).post(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='room_delete_bulk',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'body': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='this should not crash (request body on DELETE method)'
                )
            }
        ),
    )
    def delete(self, *args, **kwargs):
        """summary from docstring
        description body is here, summary is not included
        """
        pass


class SubjectList(generics.ListCreateAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    parser_classes = (FormParser, CamelCaseJSONParser, FileUploadParser)
    renderer_classes = (CamelCaseJSONRenderer,)
    swagger_schema = CamelCaseOperationIDAutoSchema

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        """post method docstring"""
        return super(SubjectList, self).post(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='subject_delete_bulk',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'body': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='this should not crash (request body on DELETE method)'
                )
            }
        ),
    )
    def delete(self, *args, **kwargs):
        """summary from docstring
        description body is here, summary is not included
        """
        pass


class OccupancyList(generics.ListCreateAPIView):
    queryset = Occupancy.objects.all()
    serializer_class = OccupancySerializer

    parser_classes = (FormParser, CamelCaseJSONParser, FileUploadParser)
    renderer_classes = (CamelCaseJSONRenderer,)
    swagger_schema = CamelCaseOperationIDAutoSchema

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        """post method docstring"""
        return super(OccupancyList, self).post(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='occupancy_delete_bulk',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'body': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='this should not crash (request body on DELETE method)'
                )
            }
        ),
    )
    def delete(self, *args, **kwargs):
        """summary from docstring
        description body is here, summary is not included
        """
        pass


class TeacherOccupancyList(generics.ListCreateAPIView):
    queryset = TeacherOccupancy.objects.all()
    serializer_class = TeacherOccupancySerializer

    parser_classes = (FormParser, CamelCaseJSONParser, FileUploadParser)
    renderer_classes = (CamelCaseJSONRenderer,)
    swagger_schema = CamelCaseOperationIDAutoSchema

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        """post method docstring"""
        return super(TeacherOccupancyList, self).post(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='occupancy_delete_bulk',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'body': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='this should not crash (request body on DELETE method)'
                )
            }
        ),
    )
    def delete(self, *args, **kwargs):
        """summary from docstring
        description body is here, summary is not included
        """
        pass


class ClassOccupancyList(generics.ListCreateAPIView):
    queryset = ClassOccupancy.objects.all()
    serializer_class = ClassOccupancySerializer

    parser_classes = (FormParser, CamelCaseJSONParser, FileUploadParser)
    renderer_classes = (CamelCaseJSONRenderer,)
    swagger_schema = CamelCaseOperationIDAutoSchema

    def perform_create(self, serializer):
        serializer.save()

    def post(self, request, *args, **kwargs):
        """post method docstring"""
        return super(ClassOccupancyList, self).post(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_id='occupancy_delete_bulk',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'body': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='this should not crash (request body on DELETE method)'
                )
            }
        ),
    )
    def delete(self, *args, **kwargs):
        """summary from docstring
        description body is here, summary is not included
        """
        pass
