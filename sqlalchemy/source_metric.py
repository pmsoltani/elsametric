from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import DECIMAL, INTEGER, VARCHAR, YEAR

from base import Base

class Source_Metric(Base):
    __tablename__ = 'source_metric'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    source_id = Column(
        INTEGER(unsigned=True), ForeignKey('source.id'), primary_key=True
    )
    type = Column(VARCHAR(45), nullable=False)
    value = Column(DECIMAL(14, 4), nullable=False)
    year = Column(YEAR(4), nullable=False)
    
    # Relationships
    source = relationship('Source', back_populates='metrics')
    
    def __init__(self, type, value, year):
        self.type = type
        self.value = value
        self.year = year