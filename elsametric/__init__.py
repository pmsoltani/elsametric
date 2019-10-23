'''elsametric package'''
__name__ = 'elsametric'
__author__ = 'Pooria Soltani'
__copyright__ = 'Copyright 2019, Pooria Soltani'
__license__ = ''
__version__ = 'v0.0.3'
__maintainer__ = 'Pooria Soltani'
__email__ = 'pooria.ms@gmail.com',
__status__ = 'Development'
__url__ = 'https://github.com/pmsoltani/elsametric'
__description__ = 'Designs a DB to store academic publications data.'


import io
import json
from pathlib import Path

from sqlalchemy_utils.functions import database_exists, create_database

with io.open(Path.cwd() / 'config.json', 'r') as config_file:
    config = json.load(config_file)

config = config['database']

TOKEN_BYTES = config['token_bytes']

DB_USER = config['startup']['mysql_user']
DB_PASS = config['startup']['mysql_pass']
DB_HOST = config['startup']['mysql_host']
DB_NAME = config['startup']['mysql_schema']
ENGINE_URI = f'mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'

if not database_exists(ENGINE_URI):
    create_database(ENGINE_URI, encoding='utf8mb4')
