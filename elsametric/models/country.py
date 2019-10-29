from sqlalchemy import CheckConstraint, Column
from sqlalchemy.orm import relationship
from sqlalchemy.types import INTEGER, VARCHAR

from .base import Base


class Country(Base):
    __tablename__ = 'country'
    # __table_args__ = (
    #     CheckConstraint('id >= 0', name='country_id_unsigned'),
    # )

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(45), nullable=False, unique=True)
    name_fa = Column(VARCHAR(45))
    domain = Column(VARCHAR(2), nullable=False, unique=True)
    region = Column(VARCHAR(10), nullable=False)
    sub_region = Column(VARCHAR(45))

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
