from sqlalchemy import Column, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER, VARCHAR

from base import Base
from associations import Source_Subject

class Source(Base):
    __tablename__ = 'source'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    id_scp = Column(BIGINT(unsigned=True), nullable=False, unique=True)
    title = Column(VARCHAR(512), nullable=False)
    url = Column(VARCHAR(256), nullable=False, unique=True)
    type = Column(VARCHAR(45), nullable=True)
    issn = Column(VARCHAR(8), nullable=True)
    e_issn = Column(VARCHAR(8), nullable=True)
    isbn = Column(VARCHAR(13), nullable=True)
    publisher = Column(VARCHAR(256), nullable=True)
    country_id = Column(
        INTEGER(unsigned=True), ForeignKey('country.id'), nullable=True)
    create_time = Column(
        DATETIME(), nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    update_time = Column(
        DATETIME(), nullable=False,
        server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    )

    # Relationships
    country = relationship('Country', back_populates='sources')
    papers = relationship('Paper', back_populates='source')
    subjects = relationship(
        'Subject', secondary=Source_Subject, back_populates='sources')

    def __init__(
        self, id_scp, title, type=None, issn=None, e_issn=None, isbn=None, 
        publisher=None, country_id=None, create_time=None, update_time=None
    ):
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