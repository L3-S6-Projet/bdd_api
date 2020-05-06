from drf_yasg.openapi import Schema, Response, TYPE_OBJECT, TYPE_STRING

from scolendar.errors import error_codes

update_response = {
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
}
