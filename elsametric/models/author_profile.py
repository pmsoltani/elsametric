from sqlalchemy import CheckConstraint, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import BIGINT, INTEGER, SMALLINT, VARCHAR

from .base import Base


class Author_Profile(Base):
    __tablename__ = 'author_profile'
    # __table_args__ = (
    #     CheckConstraint('id >= 0', name='author_profile_id_unsigned'),
    # )

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    author_id = Column(INTEGER, ForeignKey('author.id'), primary_key=True)
    address = Column(VARCHAR(256), nullable=False, unique=True)
    type = Column(VARCHAR(45), nullable=False)

    # Relationships
    author = relationship('Author', back_populates='profiles')

    def __init__(self, address: str, type: str, author_id: int = None) -> None:
        self.author_id = author_id
        self.address = address
        self.type = type

    def __repr__(self) -> str:
        return f'{self.type}: {self.address} for {self.author}'
