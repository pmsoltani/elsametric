'''elsametric package'''


import io
import json
from pathlib import Path

from sqlalchemy_utils.functions import database_exists, create_database

with io.open(Path.cwd() / 'config.json', 'r') as config_file:
    config = json.load(config_file)

config = config['database']

TOKEN_BYTES = config['token_bytes']

DIALECT = config['startup']['dialect']
assert DIALECT in ('mysql', 'postgresql')

DB_DRIVER = config['startup'][DIALECT]['driver']
DB_USER = config['startup'][DIALECT]['user']
DB_PASS = config['startup'][DIALECT]['pass']
DB_HOST = config['startup'][DIALECT]['host']
DB_NAME = config['startup'][DIALECT]['schema']

ENGINE_URI = f'{DIALECT}+{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'

if not database_exists(ENGINE_URI):
    encoding = 'utf8mb4' if DIALECT == 'mysql' else 'utf8'
    create_database(ENGINE_URI, encoding=encoding)
