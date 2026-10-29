from pathlib import Path
import os
BASE_DIR=Path(__file__).resolve().parent
SECRET_KEY=os.environ.get('DJANGO_SECRET_KEY','pharmaonto-local-academic-demo-only-2026')
DEBUG=False
ALLOWED_HOSTS=['127.0.0.1','localhost','testserver']
ROOT_URLCONF='webapp.urls'
MIDDLEWARE=['django.middleware.security.SecurityMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
INSTALLED_APPS=[]
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':False,'OPTIONS':{}}]
DATA_UPLOAD_MAX_MEMORY_SIZE=16384
CSRF_COOKIE_SAMESITE='Strict'
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS='DENY'
USE_TZ=True
DEFAULT_CHARSET='utf-8'
