"""
메듀랩 AI로봇코딩 융합학원 - Student Arcade
Django Settings
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: 배포 시 반드시 변경하세요!
SECRET_KEY = 'django-insecure-change-this-in-production-medulab-2026'

# SECURITY WARNING: 배포 시 False로 변경하세요!
DEBUG = True

ALLOWED_HOSTS = ['*']  # 배포 시 도메인으로 변경

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'arcade',
    'courses',
    'typing_practice',
    'django.contrib.sitemaps',
    'django.contrib.sites',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'medulab_arcade.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'medulab_arcade.wsgi.application'

# Database - SQLite(개발용), 배포 시 PostgreSQL 권장
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ---- 배포 시 PostgreSQL 설정 ----
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'medulab_arcade',
#         'USER': 'your_db_user',
#         'PASSWORD': 'your_db_password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (업로드된 학생 작품)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 업로드 파일 크기 제한 (50MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 로그인/로그아웃 리다이렉트
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

X_FRAME_OPTIONS = 'SAMEORIGIN'

# Sites framework ID
SITE_ID = 1

# 인증 백엔드 설정 (이메일 및 아이디 로그인 지원)
AUTHENTICATION_BACKENDS = [
    'arcade.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]