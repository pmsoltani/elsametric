from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DDL, event, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.types import BIGINT, DateTime, INTEGER, VARCHAR

from .base import Base
from .associations import Source_Subject


class Source(Base):
    __tablename__ = 'source'
    __table_args__ = (
        # CheckConstraint('id >= 0', name='source_id_unsigned'),
        CheckConstraint('id_scp >= 0', name='source_id_scp_unsigned'),
    )

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    id_scp = Column(BIGINT, nullable=False, unique=True)
    title = Column(VARCHAR(512), nullable=False)
    url = Column(VARCHAR(256), nullable=False, unique=True)
    type = Column(VARCHAR(45))
    issn = Column(VARCHAR(8))
    e_issn = Column(VARCHAR(8))
    isbn = Column(VARCHAR(13))
    publisher = Column(VARCHAR(256))
    country_id = Column(INTEGER, ForeignKey('country.id'))
    create_time = Column(
        DateTime(), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    update_time = Column(
        DateTime(), nullable=False, server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    country = relationship('Country', back_populates='sources')
    papers = relationship('Paper', back_populates='source')
    subjects = relationship(
        'Subject', secondary=Source_Subject, back_populates='sources')
    metrics = relationship('Source_Metric', back_populates='source')

    def __init__(
            self, id_scp: int, title: str, type: str = None,
            issn: str = None, e_issn: str = None, isbn: str = None,
            publisher: str = None, country_id: int = None,
            create_time: datetime = None, update_time: datetime = None
    ) -> None:
        self.id_scp = id_scp
        self.title = title
        self.url = f'https://www.scopus.com/sourceid/{id_scp}'
        self.type = type
        self.issn = issn
        self.e_issn = e_issn
        self.isbn = isbn
        self.publisher = publisher
        self.country_id = country_id
        self.create_time = create_time
        self.update_time = update_time

    def __repr__(self) -> str:
        max_len = 50
        if len(self.title) <= max_len:
            return f'{self.id_scp}: {self.title}; Type: {self.type}'
        return f'{self.id_scp}: {self.title[:max_len-3]}...; Type: {self.type}'


# update_time_trigger = DDL(
#     '''
#     CREATE OR REPLACE FUNCTION set_update_time()
#     RETURNS TRIGGER AS $$
#     BEGIN
#         NEW.update_time = now();
#         RETURN NEW;
#     END;
#     $$ language 'plpgsql';

#     CREATE TRIGGER source_update_time
#         BEFORE UPDATE ON source
#         FOR EACH ROW
#         EXECUTE PROCEDURE  set_update_time();
#     '''
# )

# event.listen(Source.__table__, 'after_create', update_time_trigger)
