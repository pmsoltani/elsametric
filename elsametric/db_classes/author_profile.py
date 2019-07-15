from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, VARCHAR

from db_classes.base import Base


class Author_Profile(Base):
    __tablename__ = 'author_profile'

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    author_id = Column(
        INTEGER(unsigned=True), ForeignKey('author.id'), primary_key=True
    )
    address = Column(VARCHAR(256), nullable=False)
    type = Column(VARCHAR(45), nullable=False)

    # Relationships
    author = relationship('Author', back_populates='profiles')

    def __init__(self, address, type, author_id=None):
        self.author_id = author_id
        self.address = address
        self.type = type

    def __repr__(self):
        return f'{self.type}: {self.address} for {self.author}'
