"""
메듀랩 AI로봇코딩 융합학원 - Student Arcade
Django Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: 배포 시 반드시 변경하세요!
SECRET_KEY = 'django-insecure-change-this-in-production-medulab-2026'

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# 로그인 도우미 잠금 해제 비밀번호 (.env의 LOGIN_HELPER_PASSWORD 로 재정의 가능)
LOGIN_HELPER_PASSWORD = os.environ.get('LOGIN_HELPER_PASSWORD', 'medu2025!')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
# 추가 Gemini API 키 (GEMINI_API_KEY_2, GEMINI_API_KEY_3 ... 최대 20개)
for _i in range(2, 21):
    _k = os.environ.get(f'GEMINI_API_KEY_{_i}', '')
    if _k:
        vars()[f'GEMINI_API_KEY_{_i}'] = _k

# SECURITY WARNING: 배포 시 False로 변경하세요!
DEBUG = True

ALLOWED_HOSTS = [
    'medulab.steam-making.com',
    'medulab.kr',
    'www.medulab.kr',
    '127.0.0.1',
    'localhost',
]

CSRF_TRUSTED_ORIGINS = [
    'https://medulab.steam-making.com',
    'https://medulab.kr',
    'https://www.medulab.kr',
]

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
                'arcade.context_processors.nav_items',
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

# 브라우저 종료 시 자동 로그아웃 (세션 쿠키 만료)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True