from datetime import datetime

from sqlalchemy import Column, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import \
    BIGINT, DATETIME, DECIMAL, INTEGER, VARCHAR

from .base import Base, token_generator, VARCHAR_COLUMN_LENGTH


class Institution(Base):
    __tablename__ = 'institution'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    id_scp = Column(BIGINT(unsigned=True), nullable=False, unique=True)
    id_frontend = Column(
        VARCHAR(VARCHAR_COLUMN_LENGTH), nullable=False, unique=True)
    name = Column(VARCHAR(128), nullable=False)
    name_fa = Column(VARCHAR(128), nullable=True)
    abbreviation = Column(VARCHAR(45), nullable=True)
    city = Column(VARCHAR(45), nullable=True)
    country_id = Column(
        INTEGER(unsigned=True), ForeignKey('country.id'), nullable=True)
    url = Column(VARCHAR(256), nullable=True, unique=True)
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
    country = relationship('Country', back_populates='institutions')
    departments = relationship('Department', back_populates='institution')
    # aliases = relationship('Institution_Alias', back_populates='institution')

    def __init__(
            self, id_scp: int, name: str, name_fa: str = None,
            abbreviation: str = None,
            city: str = None, country_id: int = None, url: str = None,
            type: str = None, lat: float = None, lng: float = None,
            create_time: datetime = None, update_time: datetime = None
    ) -> None:
        self.id_scp = id_scp
        self.id_frontend = token_generator()
        self.name = name
        self.name_fa = name_fa
        self.abbreviation = abbreviation
        self.city = city
        self.country_id = country_id
        self.url = url
        self.type = type
        self.lat = lat
        self.lng = lng
        self.create_time = create_time
        self.update_time = update_time

    def __repr__(self) -> str:
        max_len = 50
        if len(self.name) <= max_len:
            return f'{self.id_scp}: {self.name}'
        return f'{self.id_scp}: {self.name[:max_len-3]}...'
