import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']


class ProductionConfig(Config):
    DEBUG = False
    PROTOCOL = 'https'


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    PROTOCOL = 'http'


class TestingConfig(Config):
    TESTING = True
