from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR

from base import Base

class Country(Base):
    __tablename__ = 'country'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    name = Column(VARCHAR(45), nullable=False, unique=True)
    domain = Column(VARCHAR(2), nullable=False, unique=True)
    region = Column(VARCHAR(10), nullable=False)
    sub_region = Column(VARCHAR(45), nullable=True)
    
    # Relationships
    sources = relationship('Source', back_populates='country')
    institutions = relationship('Institution', back_populates='country')
    
    def __init__(self, name, domain, region, sub_region=None):
        self.name = name
        self.domain = domain
        self.region = region
        self.sub_region = sub_region