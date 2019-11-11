'''elsametric package'''


import io
import json
from pathlib import Path

from environs import Env

from sqlalchemy_utils.functions import database_exists, create_database

env = Env()
env.read_env(path=Path.cwd())
# 'path' argument is needed for when elsametric is called from another module.

with env.prefixed('DB_'):
    TOKEN_BYTES = env.int('TOKEN_BYTES')
    DIALECT = env('DIALECT')
    if DIALECT.lower() not in ('mysql', 'postgresql'):
        raise ValueError('Invalid configuration for "DIALECT"')

    with env.prefixed(f'{DIALECT.upper()}_'):
        DB_DRIVER = env('DRIVER')
        DB_USER = env('USER')
        DB_PASS = env('PASS')
        DB_HOST = env('HOST')
        DB_NAME = env('SCHEMA')

ENGINE_URI = f'{DIALECT}+{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'

if not database_exists(ENGINE_URI):
    encoding = 'utf8mb4' if DIALECT == 'mysql' else 'utf8'
    create_database(ENGINE_URI, encoding=encoding)
