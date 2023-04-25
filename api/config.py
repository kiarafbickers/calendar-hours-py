import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')

class ProductionConfig(Config):
    DEBUG = False
    DATABASE_URI = os.environ.get('PRODUCTION_DATABASE_URI')
    DATABASE_NAME = os.environ.get('PRODUCTION_DATABASE_NAME')

class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URI = os.environ.get('DEVELOPMENT_DATABASE_URI')
    DATABASE_NAME = os.environ.get('DEVELOPMENT_DATABASE_NAME')
    APPLICATION_TYPE = os.environ.get('DEVELOPMENT_APPLICATION_TYPE')
    CLIENT_ID = os.environ.get('DEVELOPMENT_CLIENT_ID')
    PROJECT_ID = os.environ.get('DEVELOPMENT_PROJECT_ID')
    AUTH_URI = os.environ.get('DEVELOPMENT_AUTH_URI')
    TOKEN_URI = os.environ.get('DEVELOPMENT_TOKEN_URI')
    AUTH_PROVIDER_X509_CERT_URL = os.environ.get('DEVELOPMENT_AUTH_PROVIDER_X509_CERT_URL')
    CLIENT_SECRET = os.environ.get('DEVELOPMENT_CLIENT_SECRET')
    REDIRECT_URIS = os.environ.get('DEVELOPMENT_REDIRECT_URIS')

    COOKIE_KEY = os.environ.get('DEVELOPMENT_COOKIE_KEY')

# Determine which config to use based on the environment variable
if os.environ.get('FLASK_ENV') == 'production':
    app_config = ProductionConfig
else:
    app_config = DevelopmentConfig
