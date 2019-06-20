from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, SMALLINT

from base import Base

Source_Subject = Table(
    'source_subject',
    Base.metadata,
    Column('source_id', INTEGER(unsigned=True), ForeignKey('source.id')),
    Column('subject_id', INTEGER(unsigned=True), ForeignKey('subject.id'))
)

Paper_Keyword = Table(
    'paper_keyword',
    Base.metadata,
    Column('paper_id', INTEGER(unsigned=True), ForeignKey('paper.id')),
    Column('keyword_id', BIGINT(unsigned=True), ForeignKey('keyword.id'))
)

Author_Department = Table(
    'author_department',
    Base.metadata,
    Column('author_id', INTEGER(unsigned=True), ForeignKey('author.id')),
    Column(
        'department_id', INTEGER(unsigned=True), ForeignKey('department.id')
    ),
    Column(
        'institution_id', INTEGER(unsigned=True), 
        ForeignKey('department.institution_id')
    )
)

class Paper_Author(Base):
    __tablename__ = 'paper_author'
    Column(
        'paper_id', INTEGER(unsigned=True), 
        ForeignKey('paper.id'), primary_key=True
    )
    Column(
        'author_id', INTEGER(unsigned=True), 
        ForeignKey('author.id'), primary_key=True
    )
    Column('author_no', SMALLINT(unsigned=True), nullable=False)

    # Relationships
    paper = relationship('Paper', back_populates='authors')
    author = relationship('Author', back_populates='papers')

    def __init__(self, author_no, paper=None, author=None):
        self.paper = paper
        self.author = author
        self.author_no = author_no