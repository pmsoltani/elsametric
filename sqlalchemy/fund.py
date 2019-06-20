from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR

from base import Base

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
    
    def __init__(self, id_scp=None, agency=None, agency_acronym=None):
        self.id_scp = id_scp
        self.agency = agency
        self.agency_acronym = agency_acronym