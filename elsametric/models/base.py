import secrets

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .. import ENGINE_URI, TOKEN_BYTES


engine = create_engine(ENGINE_URI)
Session = sessionmaker(bind=engine)

Base = declarative_base()


# Helper function to generate tokens with 'TOKEN_BYTES' for 'id_front' columns
def token_generator(nbytes=TOKEN_BYTES):
    return secrets.token_urlsafe(nbytes)


# Import the following constant in modules employing `token_generator`. Note:
# The text is Base64 encoded, so each byte is 4/3 chars.
VARCHAR_COLUMN_LENGTH = -(-4 * TOKEN_BYTES // 3)  # ceiling division
