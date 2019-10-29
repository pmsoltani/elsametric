from sqlalchemy import CheckConstraint, Column
from sqlalchemy.orm import relationship
from sqlalchemy.types import INTEGER, VARCHAR

from .base import Base
from .associations import Source_Subject


class Subject(Base):
    __tablename__ = 'subject'
    __table_args__ = (
        # CheckConstraint('id >= 0', name='subject_id_unsigned'),
        CheckConstraint('asjc >= 0', name='subject_asjc_unsigned'),
    )

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    asjc = Column(INTEGER, nullable=False, unique=True)
    top = Column(VARCHAR(128), nullable=False)
    middle = Column(VARCHAR(128), nullable=False)
    low = Column(VARCHAR(128), nullable=False)

    # Relationships
    sources = relationship(
        'Source', secondary=Source_Subject, back_populates='subjects')

    def __init__(self, asjc: int, top: str, middle: str, low: str) -> None:
        self.asjc = asjc
        self.top = top
        self.middle = middle
        self.low = low

    def __repr__(self) -> str:
        return f'{self.asjc}: {self.low}'
