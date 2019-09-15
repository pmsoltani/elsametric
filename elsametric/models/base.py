import os
import json
import secrets

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

path = os.path.abspath(__file__)
for d in range(3):  # going up 2 directories
    path = os.path.dirname(path)

config_path = os.path.join(path, 'config.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

db_user = config['MySQL User']
db_pass = config['MySQL Pass']
db_host = config['MySQL Host']
db_schema = config['MySQL Schema']
engine_uri = f'mysql+mysqlconnector://{db_user}:{db_pass}@{db_host}/{db_schema}'

engine = create_engine(engine_uri)
Session = sessionmaker(bind=engine)

Base = declarative_base()


# Helper function to generate 8-bytes tokens for 'id_front' columns
# The text is Base64 encoded, so each byte is 1.3 chars (Total 11 chars).
def token_generator(nbytes=8):
    return secrets.token_urlsafe(nbytes)
