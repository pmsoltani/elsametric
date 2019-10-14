import os
import json

from sqlalchemy_utils.functions import database_exists, create_database

config_path = os.path.join(os.getcwd(), 'config.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

config = config['database']['startup']

db_user = config['MySQL User']
db_pass = config['MySQL Pass']
db_host = config['MySQL Host']
db_name = config['MySQL Schema']
engine_uri = f'mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_name}'

if not database_exists(engine_uri):
    create_database(engine_uri)
