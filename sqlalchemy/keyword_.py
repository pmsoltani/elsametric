from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR

from base import Base, Session, engine
from associations import paper_keyword

class Keyword(Base):
    __tablename__ = 'keyword'

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    keyword = Column(VARCHAR(256), nullable=False, unique=True)
    
    # Relationships
    papers = relationship(
        'Paper', secondary=paper_keyword, back_populates='keywords')
    
    def __init__(self, keyword):
        self.keyword = keyword