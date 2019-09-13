from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import DECIMAL, INTEGER, VARCHAR, YEAR

from elsametric.db_classes.base import Base


class Source_Metric(Base):
    __tablename__ = 'source_metric'
    __table_args__ = (
        UniqueConstraint(
            'source_id', 'type', 'year',
            name='uq_sourcemetric_sourceid_type_year'
        ),
    )

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    source_id = Column(
        INTEGER(unsigned=True),
        ForeignKey('source.id'), primary_key=True, nullable=False
    )
    type = Column(VARCHAR(45), nullable=False)
    value = Column(DECIMAL(13, 3), nullable=False)
    year = Column(YEAR(4), nullable=False)

    # Relationships
    source = relationship('Source', back_populates='metrics')

    def __init__(self, type, value, year):
        self.type = type
        self.value = value
        self.year = year

    def __repr__(self):
        if self.is_integer():
            return f'{self.type} {self.year}: {int(self.value)}'
        return f'{self.type} {self.year}: {self.value}'

    def is_integer(self):
        return float(self.value).is_integer()
