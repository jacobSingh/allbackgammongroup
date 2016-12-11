class Config(object):
    DEBUG = False
    TESTING = False
    DATABASE_URI = 'sqlite://:memory:'
    DATA_DIR = "../data"
    XP_THRESHOLD = 200

class ProductionConfig(Config):
    DATABASE_URI = 'mysql://user@localhost/foo'
    DATA_DIR = "../datap"

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
