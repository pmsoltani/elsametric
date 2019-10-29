from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DDL, event, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.types import BIGINT, DateTime, DECIMAL, INTEGER, VARCHAR

from .base import (
    Base,
    DIALECT,
    token_generator,
    UPDATE_TIME_DEFAULT,
    VARCHAR_COLUMN_LENGTH
)


class Institution(Base):
    __tablename__ = 'institution'
    __table_args__ = (
        CheckConstraint(
            'id >= 0',
            name='institution_id_unsigned'
        ) if DIALECT == "postgresql" else None,
        CheckConstraint('id_scp >= 0', name='institution_id_scp_unsigned'),
    )

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    id_scp = Column(BIGINT, nullable=False, unique=True)
    id_frontend = Column(
        VARCHAR(VARCHAR_COLUMN_LENGTH), nullable=False, unique=True)
    name = Column(VARCHAR(128), nullable=False)
    name_fa = Column(VARCHAR(128))
    abbreviation = Column(VARCHAR(45))
    city = Column(VARCHAR(45))
    country_id = Column(INTEGER, ForeignKey('country.id'))
    url = Column(VARCHAR(256), unique=True)
    type = Column(VARCHAR(45))
    lat = Column(DECIMAL(8, 6))
    lng = Column(DECIMAL(9, 6))
    create_time = Column(
        DateTime(), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    update_time = Column(
        DateTime(), nullable=False, server_default=text(UPDATE_TIME_DEFAULT))

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


if DIALECT == "postgresql":
    update_time_trigger = DDL(
        '''
        CREATE OR REPLACE FUNCTION set_update_time()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.update_time = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        CREATE TRIGGER institution_update_time
            BEFORE UPDATE ON institution
            FOR EACH ROW
            EXECUTE PROCEDURE  set_update_time();
        '''
    )

    event.listen(Institution.__table__, 'after_create', update_time_trigger)
