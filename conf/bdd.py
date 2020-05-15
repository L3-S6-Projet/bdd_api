import os
from typing import Union, Dict, Optional


def get_db_info(BASE_DIR: str) -> Union[Dict[str, Dict[str, str]], Dict[str, Dict[str, Optional[str]]], None]:
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_NAME = os.getenv('DB_NAME', 'scolendar')
    if os.getenv('TRAVIS', None):
        return {
            'default': {
                'NAME': DB_NAME,
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'USER': 'postgres',
                'PASSWORD': '',
                'HOST': DB_HOST,
            },
        }
    if os.getenv('IN_DOCKER', 0) in [1, '1']:
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        return {
            'default': {
                'NAME': DB_NAME,
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'USER': DB_USER,
                'PASSWORD': DB_PASSWORD,
                'HOST': DB_HOST,
            },
        }
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
