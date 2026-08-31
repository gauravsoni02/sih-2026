from .base import *  # noqa: F401, F403

import dj_database_url
from decouple import config

DEBUG = True

DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
        },
    }

CORS_ALLOW_ALL_ORIGINS = True
