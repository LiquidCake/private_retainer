import os
from dotenv import load_dotenv
from logging.config import dictConfig
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_caching import Cache

env_file_override = os.environ.get('ENV_FILE_PATH')

load_dotenv(env_file_override if env_file_override else '.env')

config = {
    'SECRET_KEY': os.urandom(12).hex(),
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'SQLALCHEMY_DATABASE_URI': 'postgresql://' + os.environ.get('POSTGRES_USER') + ':' + os.environ.get('POSTGRES_PASSWORD') \
    + '@' + os.environ.get('POSTGRES_HOST') + ':' + os.environ.get('POSTGRES_PORT') + '/' + os.environ.get('POSTGRES_DB')
}

app = Flask(__name__)
app.config.from_mapping(config)

auth = HTTPBasicAuth()
cache = Cache(app)

db = SQLAlchemy()
db.init_app(app)

#logging.basicConfig()
# sql queries logging
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        'ROOT': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

dictConfig(LOGGING_CONFIG)

from scrapper_webapp import routes
