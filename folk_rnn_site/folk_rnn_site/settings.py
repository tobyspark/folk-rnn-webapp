"""
Django settings for folk_rnn_site project.

Generated by 'django-admin startproject' using Django 1.11.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

if 'FOLKRNN_PRODUCTION' in os.environ:
    DEBUG = False
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
    ALLOWED_HOSTS = [os.environ['COMPOSER_HOST'], os.environ['ARCHIVER_HOST']]
else:
    DEBUG = True  
    SECRET_KEY = 'h0rpwz_a*dows+-gzl5a)8ev5^_rmx($tby=y6ep5x_b5*7w56'
    ALLOWED_HOSTS = [
                '127.0.0.1',
                'folkrnn.org',
                'themachinefolksession.org',
                'folkrnn.org.local',
                'themachinefolksession.org.local',
                ]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'widget_tweaks',
    'django_hosts',
    'channels',
    'composer',
    'archiver',
    'backup',
]

MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware'
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],
        },
    },
}

ROOT_HOSTCONF = 'folk_rnn_site.hosts'
DEFAULT_HOST = 'composer'
ROOT_URLCONF = 'composer.urls'

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

WSGI_APPLICATION = 'folk_rnn_site.wsgi.application'
ASGI_APPLICATION = "folk_rnn_site.routing.application"

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'folk_rnn',
        'USER': 'folk_rnn',
        'PASSWORD': os.environ['POSTGRES_PASS'] if 'POSTGRES_PASS' in os.environ else 'dbpass',
        'HOST': '',
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

## Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'as_per_channels': {
            # https://github.com/django/channels/blob/master/channels/log.py#L12
            'format': '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
        },
        'use': {
            'format': '%(asctime)s %(session)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'as_per_channels', 
        },
        'file_composer_use': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/folk_rnn_webapp/composer.use.log',
            'formatter': 'use',
        },
    },
    'loggers': {
        'composer': {
            'handlers': ['console'],
            'level': 'WARNING' if 'FOLKRNN_PRODUCTION' in os.environ else 'DEBUG',
        },
        'composer.use': {
            'handlers': ['file_composer_use'],
            'level': 'DEBUG',
        },
        'backup': {
            'handlers': ['console'],
            'level': 'WARNING' if 'FOLKRNN_PRODUCTION' in os.environ else 'DEBUG',
        },
    },
}


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/folk_rnn_static/'
STATICFILES_DIRS = [
    '/folk_rnn_sf/',
]

# URLS not in URLConf. (This isn't good)
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
