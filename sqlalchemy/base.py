import json

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

with open('config.json', 'r') as read_file:
    client = json.load(read_file)

mysql_user = client['MySQL User']
mysql_pass = client['MySQL Pass']
mysql_host = 'localhost'
mysql_db = 'scopus3'
engine_uri = f'mysql+mysqlconnector://{mysql_user}:{mysql_pass}@{mysql_host}/{mysql_db}'

engine = create_engine(engine_uri)
Session = sessionmaker(bind=engine)

Base = declarative_base()