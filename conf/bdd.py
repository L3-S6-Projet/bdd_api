import os
import subprocess
from platform import system


def get_db_info(BASE_DIR: str) -> dict:
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_NAME = os.getenv('DB_NAME', 'enseign')
    if os.getenv('TRAVIS', None):
        return {
            'default': {
                'NAME': DB_NAME,
                'ENGINE': 'django.db.backends.mysql',
                'USER': 'travis',
                'PASSWORD': '',
                'HOST': DB_HOST,
            },
        }
    if system() == 'Linux':
        sp = subprocess.Popen('./check_mysql.sh', stdout=subprocess.PIPE)
        if sp.returncode == 0:
            return {
                'default': {
                    'NAME': DB_NAME,
                    'ENGINE': 'django.db.backends.mysql',
                    'USER': os.getenv('DB_USER'),
                    'PASSWORD': os.getenv('DB_PASSWORD'),
                    'HOST': DB_HOST,
                },
            }
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
