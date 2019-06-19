from sqlalchemy import Column, Table, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER, VARCHAR

from base import Base, Session, engine

source_subject = Table(
    'source_subject',
    Base.metadata,
    Column('source_id', INTEGER(unsigned=True), ForeignKey('source.id')),
    Column('subject_id', INTEGER(unsigned=True), ForeignKey('subject.id'))
)

paper_keyword = Table(
    'paper_keyword',
    Base.metadata,
    Column('paper_id', INTEGER(unsigned=True), ForeignKey('paper.id')),
    Column('keyword_id', BIGINT(unsigned=True), ForeignKey('keyword.id'))
)