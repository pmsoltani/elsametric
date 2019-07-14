from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR

from db_classes.base import Base
from db_classes.associations import Source_Subject

class Subject(Base):
    __tablename__ = 'subject'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    asjc = Column(INTEGER(unsigned=True), nullable=False, unique=True)
    top = Column(VARCHAR(128), nullable=False)
    middle = Column(VARCHAR(128), nullable=False)
    low = Column(VARCHAR(128), nullable=False)

    # Relationships
    sources = relationship(
        'Source', secondary=Source_Subject, back_populates='subjects')

    def __init__(self, asjc, top, middle, low):
        self.asjc = asjc
        self.top = top
        self.middle = middle
        self.low = low
