# import datetime
from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import \
    BIGINT, BOOLEAN, DATE, DATETIME, DECIMAL, INTEGER, SMALLINT, \
    TEXT, TIME, TIMESTAMP, TINYINT, VARCHAR, YEAR

from base import Base, Session, engine

class Fund(Base):
    __tablename__ = 'fund'

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    id_scp = Column(VARCHAR(45), nullable=True, unique=True)
    agency = Column(VARCHAR(256), nullable=True)
    agency_acronym = Column(VARCHAR(20), nullable=True)
    
    # Relationships
    papers = relationship('Paper', back_populates='fund')
    
    # actors = relationship("Actor", secondary=movies_actors_association)

    def __init__(self, id_scp=None, agency=None, agency_acronym=None):
        self.id_scp = id_scp
        self.agency = agency
        self.agency_acronym = agency_acronym

# Base.metadata.create_all(engine)
# session = Session()

# d1 = Paper(
#     id_scp=1,
#     eid='1',
#     title='abc',
#     type='ab',
#     total_author=3,
#     open_access=2,
#     cited_cnt=5,
#     url='www',
#     date='2019-02-03 12:20:20',
#     retrieval_time='2017-01-01',
# )