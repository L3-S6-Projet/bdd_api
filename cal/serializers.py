from django.utils.translation import gettext as _
from rest_framework import serializers

from cal.models import Class, Rooms, Subject, Occupancy, TeacherOccupancy, ClassOccupancy, years
from users.models import UserInfo


class ClassSerializer(serializers.ModelSerializer):
    year = serializers.ChoiceField(choices=years, default=_('L1'), help_text=_('Année en cours'))

    def create(self, validated_data):
        validated_data['name'] = validated_data['name'].title()
        return Class.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.years = validated_data.get('year', instance.years)
        instance.save()
        return instance

    class Meta:
        model = Class
        fields = [
            'id',
            'name',
            'year',
        ]


class RoomSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(min_value=0)

    def create(self, validated_data):
        return Class.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.capacity = validated_data.get('capacity', instance.capacity)
        instance.save()
        return instance

    class Meta:
        model = Rooms
        fields = [
            'id',
            'name',
            'capacity',
        ]


class SubjectSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return Subject.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance

    class Meta:
        model = Subject
        fields = [
            'id',
            'name',
        ]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = [
            'user.first_name',
            'user.last_name',
            'type',
        ]


class CalUserOccupancySerializer(serializers.ModelSerializer):
    obj = UserSerializer(many=False, read_only=True)

    def create(self, validated_data):
        return Occupancy.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.occupancy = validated_data.get('occupancy', instance.occupancy)
        instance.obj = validated_data.get('obj', instance.obj)
        instance.save()
        return instance

    class Meta:
        model = TeacherOccupancy
        fields = [
            'obj',
        ]


class ClassOccupancySerializer(serializers.ModelSerializer):
    obj = ClassSerializer(many=False, read_only=True)

    def create(self, validated_data):
        return Occupancy.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.occupancy = validated_data.get('occupancy', instance.occupancy)
        instance.obj = validated_data.get('obj', instance.obj)
        instance.save()
        return instance

    class Meta:
        model = ClassOccupancy
        fields = [
            'obj',
        ]


class OccupancySerializer(serializers.ModelSerializer):
    teachers = CalUserOccupancySerializer(many=True)
    classes = ClassOccupancySerializer(many=True)

    def create(self, validated_data):
        occupancy = Occupancy.objects.create(**validated_data)
        teachers_data = validated_data.pop('teachers')
        for teacher_data in teachers_data:
            TeacherOccupancy.objects.create(occupancy=occupancy, **teacher_data)
        classes_data = validated_data.pop('classes')
        for class_data in classes_data:
            ClassOccupancy.objects.create(occupancy=occupancy, **class_data)
        return occupancy

    def update(self, instance, validated_data):
        instance.room = validated_data.get('room', instance.room)
        instance.date = validated_data.get('date', instance.date)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.duration = validated_data.get('duration', instance.duration)
        instance.subject = validated_data.get('subject', instance.subject)
        instance.session_types = validated_data.get('session_type', instance.session_types)

        instance.save()

        teachers_data = validated_data.pop('teachers')
        if teachers_data:
            for teacher_data in teachers_data:
                teacher_object = TeacherOccupancy.objects.filter(occupancy=instance, obj=teacher_data['obj'])
                if len(teacher_object) > 0:
                    pass
                else:
                    TeacherOccupancy.objects.create(occupancy=instance, **teacher_data)

        classes_data = validated_data.pop('classes')
        if classes_data:
            for class_data in classes_data:
                class_object = ClassOccupancy.objects.filter(occupancy=instance, obj=class_data['obj'])
                if len(class_object) > 0:
                    pass
                else:
                    ClassOccupancy.objects.create(occupancy=instance, **class_data)

        return instance

    class Meta:
        model = Occupancy
        fields = [
            'id',
            'room',
            'date',
            'start_time',
            'duration',
            'subject',
            'session_type',
            'teachers',
            'classes'
        ]
