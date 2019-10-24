from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR

from .base import Base


class Country(Base):
    __tablename__ = 'country'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    name = Column(VARCHAR(45), nullable=False, unique=True)
    name_fa = Column(VARCHAR(45), nullable=True)
    domain = Column(VARCHAR(2), nullable=False, unique=True)
    region = Column(VARCHAR(10), nullable=False)
    sub_region = Column(VARCHAR(45), nullable=True)

    # Relationships
    sources = relationship('Source', back_populates='country')
    institutions = relationship('Institution', back_populates='country')

    def __init__(self, name: str,
                 domain: str, region: str, sub_region: str = None) -> None:
        self.name = name
        self.domain = domain
        self.region = region
        self.sub_region = sub_region

    def __repr__(self) -> str:
        return f'{self.domain}: {self.name}'
