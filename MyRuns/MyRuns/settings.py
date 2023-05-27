"""
Django settings for MyRuns project.

Generated by 'django-admin startproject' using Django 1.8.18.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import mimetypes 
from pathlib import Path
import platform
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#print('BASE_DIR=',BASE_DIR)
#print ('uname=',platform.uname())

# load_dotenv(BASE_DIR + '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', '')

# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = os.getenv('DEBUG', '0').lower() in ['true', 't', '1']
DEBUG = 1

#ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(' ')
ALLOWED_HOSTS = '*'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

#ALLOWED_HOSTS = ['192.168.1.68','fakarava94.no-ip.org']
CORS_ORIGIN_ALLOW_ALL = True


# Application definition

INSTALLED_APPS = (
    'strava2.apps.Strava2Config',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'strava',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'celery_progress',
    'channels',
    'daphne',
)

MIDDLEWARE = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

ROOT_URLCONF = 'MyRuns.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

#WSGI_APPLICATION = 'MyRuns.wsgi.application'
ASGI_APPLICATION = 'MyRuns.asgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
# postgres://fli:wzRuxiiK4sF0XlkwuRdTsb6VyY58uwQw@dpg-cgecj6pmbg58c1eg129g-a/myruns

DATABASE_URL = os.environ.get('DATABASE_URL', '')
# ex: postgres://fli:iqNFrdrffHXrcceCkDunnK1yfkyIaOOL@dpg-ch1fcrceoogo6oihajeg-a/myruns_en73
url=DATABASE_URL.split('//')[1]
database_user=url.split(':')[0]
database_passwd=url.split(':')[1].split('/')[0].split('@')[0]
database_host=url.split(':')[1].split('/')[0].split('@')[1]
database_name=url.split(':')[1].split('/')[1]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': database_name,
        'USER': database_user,
        'PASSWORD': database_passwd,
        'HOST': database_host,
        'PORT': '',
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

#USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': (
       'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
   ),
       'PAGE_SIZE': 10
}

CELERY_BEAT_SCHEDULE = {
    'check-celery-avalibility': {
        'task': 'checkCeleryAvailibility',
        'schedule': 200.0,
        'options': {
            'expires': 30.0
        }
    }
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
             'hosts': [('red-cgfemmo2qv28tc6t5v6g', 6379)],
             #'hosts': [('localhost', 6379)],
        },
    }
}
ASGI_APPLICATION = "MyRuns.routing.application"

ANGULAR_APP_DIR = os.path.join(BASE_DIR, 'frontend/dist')
SVG_DIR = os.path.join(BASE_DIR, 'static/assets')

print ('SVG_DIR=',SVG_DIR)

STATICFILES_DIRS = [
     SVG_DIR,
    os.path.join(ANGULAR_APP_DIR),
]   

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

mimetypes.add_type("assets/svg+xml", ".svg", True)
#print('mimetypes: ',mimetypes.guess_type('assets/run.svg'))

