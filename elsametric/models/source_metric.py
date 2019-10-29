from sqlalchemy import CheckConstraint, Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.types import DECIMAL, INTEGER, VARCHAR

from .base import Base


class Source_Metric(Base):
    __tablename__ = 'source_metric'
    __table_args__ = (
        # CheckConstraint('id >= 0', name='source_metric_id_unsigned'),
        CheckConstraint('year >= 1970 AND year <= 2069', name='year_range'),
        UniqueConstraint(
            'source_id', 'type', 'year', name='uq_sourceid_type_year'),
    )

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    source_id = Column(INTEGER, ForeignKey('source.id'), primary_key=True)
    type = Column(VARCHAR(45), nullable=False)
    value = Column(DECIMAL(13, 3), nullable=False)
    year = Column(INTEGER, nullable=False)

    # Relationships
    source = relationship('Source', back_populates='metrics')

    def __init__(self, type: str, value: float, year: int) -> None:
        self.type = type
        self.value = value
        self.year = year

    def __repr__(self) -> str:
        if self.is_integer():
            return f'{self.type} {self.year}: {int(self.value)}'
        return f'{self.type} {self.year}: {self.value}'

    def is_integer(self) -> bool:
        return float(self.value).is_integer()
