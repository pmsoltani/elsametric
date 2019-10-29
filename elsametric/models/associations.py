from sqlalchemy import (
    Column,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import BIGINT, INTEGER, SMALLINT

from .base import Base, DIALECT

Source_Subject = Table(
    'source_subject', Base.metadata,
    Column('source_id', INTEGER, ForeignKey('source.id'), primary_key=True),
    Column('subject_id', INTEGER, ForeignKey('subject.id'), primary_key=True)
)

Paper_Keyword = Table(
    'paper_keyword', Base.metadata,
    Column('paper_id', INTEGER, ForeignKey('paper.id'), primary_key=True),
    Column('keyword_id', BIGINT, ForeignKey('keyword.id'), primary_key=True)
)

Author_Department = Table(
    'author_department', Base.metadata,
    Column('author_id', INTEGER, ForeignKey('author.id'), primary_key=True),
    Column('department_id', INTEGER, primary_key=True),
    Column('institution_id', INTEGER, primary_key=True),
    ForeignKeyConstraint(
        ('department_id', 'institution_id'),
        ('department.id', 'department.institution_id'),
    )
)


class Paper_Author(Base):
    __tablename__ = 'paper_author'
    __table_args__ = (
        CheckConstraint('author_no >= 0', name='author_no_unsigned'),
    )

    paper_id = Column(INTEGER, ForeignKey('paper.id'), primary_key=True)
    author_id = Column(INTEGER, ForeignKey('author.id'), primary_key=True)
    author_no = Column(SMALLINT, nullable=False)

    # Relationships
    paper = relationship('Paper', back_populates='authors')
    author = relationship('Author', back_populates='papers')

    def __init__(self, author_no: int) -> None:
        self.author_no = author_no

    def __repr__(self) -> str:
        return f'{self.paper} <-> {self.author}'
