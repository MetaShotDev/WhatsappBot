import os
from dotenv import load_dotenv


load_dotenv()



SECRET_KEY = os.environ.get("SECRET_KEY")



ALLOWED_HOSTS = ["*"]

CORS_ALLOW_HEADERS = ['*']

CORS_ALLOW_ALL_ORIGINS = True



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST':os.getenv("DB_HOST"),
        'PORT':os.getenv("DB_PORT"),
    }
}
