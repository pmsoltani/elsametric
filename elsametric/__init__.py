'''elsametric package'''


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
