from drf_yasg.openapi import Schema, TYPE_OBJECT, TYPE_ARRAY, TYPE_STRING, TYPE_BOOLEAN, TYPE_INTEGER

from scolendar.models import occupancy_list

teacher_list_schema = Schema(
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
)

occupancies_schema = Schema(
    title='Occupancies',
    type=TYPE_OBJECT,
    properties={
        'status': Schema(type=TYPE_STRING, example='success'),
        'days': Schema(
            type=TYPE_ARRAY,
            items=Schema(
                type=TYPE_OBJECT,
                properties={
                    'date': Schema(type=TYPE_STRING, example='05-01-2020'),
                    'occupancies': Schema(
                        type=TYPE_ARRAY,
                        items=Schema(
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
                                'name': Schema(type=TYPE_STRING,
                                               example='Algorithmique TP Groupe 1'),
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
                    ),
                },
                required=['date', 'occupancies', ]
            )
        ),
    },
    required=['status', 'days', ]
)
