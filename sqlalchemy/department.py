from sqlalchemy import Column, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import DATETIME, DECIMAL, INTEGER, VARCHAR

from base import Base
from associations import Author_Department

class Department(Base):
    __tablename__ = 'department'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    institution_id = Column(
        INTEGER(unsigned=True), ForeignKey('institution.id'), primary_key=True)
    name = Column(VARCHAR(128), nullable=False)
    abbreviation = Column(VARCHAR(20), nullable=True)
    type = Column(VARCHAR(45), nullable=True)
    lat = Column(DECIMAL(8, 6), nullable=True)
    lng = Column(DECIMAL(9, 6), nullable=True)
    create_time = Column(
        DATETIME(), nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    update_time = Column(
        DATETIME(), nullable=False,
        server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    )

    # Relationships
    institution = relationship('Institution', back_populates='departments')
    aliases = relationship('Department_Alias', back_populates='department')
    authors = relationship(
        'Author', secondary=Author_Department, back_populates='departments')

    def __init__(
        self, name, institution_id=None, abbreviation=None, type=None, 
        lat=None, lng=None, create_time=None, update_time=None
    ):
        self.institution_id = institution_id
        self.name = name
        self.abbreviation = abbreviation
        self.type = type
        self.lat = lat
        self.lng = lng
        self.create_time = create_time
        self.update_time = update_time