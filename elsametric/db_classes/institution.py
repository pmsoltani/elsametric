from sqlalchemy import Column, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import \
    BIGINT, DATETIME, DECIMAL, INTEGER, VARCHAR

from elsametric.db_classes.base import Base, token_generator


class Institution(Base):
    __tablename__ = 'institution'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    id_scp = Column(BIGINT(unsigned=True), nullable=False, unique=True)
    id_frontend = Column(VARCHAR(16), nullable=False, unique=True)
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
            self, id_scp, name, abbreviation=None, city=None, country_id=None,
            url=None, type=None, lat=None, lng=None,
            create_time=None, update_time=None
    ):
        self.id_scp = id_scp
        self.id_frontend = token_generator()
        self.name = name
        self.abbreviation = abbreviation
        self.city = city
        self.country_id = country_id
        self.url = url
        self.type = type
        self.lat = lat
        self.lng = lng
        self.create_time = create_time
        self.update_time = update_time

    def __repr__(self):
        max_len = 50
        if len(self.name) <= max_len:
            return f'{self.id_scp}: {self.name}'
        return f'{self.id_scp}: {self.name[:max_len-3]}...'
