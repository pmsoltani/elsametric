from datetime import datetime, date

from sqlalchemy import CheckConstraint, Column, DDL, event, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.types import (
    BIGINT,
    BOOLEAN,
    DATE,
    DateTime,
    INTEGER,
    SMALLINT,
    TEXT,
    VARCHAR
)

from .base import Base, DIALECT, UPDATE_TIME_DEFAULT
from .associations import Paper_Keyword, Paper_Author


class Paper(Base):
    __tablename__ = 'paper'
    __table_args__ = (
        CheckConstraint(
            'id >= 0',
            name='paper_id_unsigned'
        ) if DIALECT == "postgresql" else None,
        CheckConstraint('id_scp >= 0', name='paper_id_scp_unsigned'),
        CheckConstraint('total_author >= 0', name='total_author_unsigned'),
        CheckConstraint('cited_cnt >= 0', name='cited_cnt_unsigned'),
    )

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    id_scp = Column(BIGINT, nullable=False, unique=True)
    eid = Column(VARCHAR(45), nullable=False, unique=True)
    title = Column(VARCHAR(512), nullable=False)
    type = Column(VARCHAR(2), nullable=False)
    type_description = Column(VARCHAR(45))
    abstract = Column(TEXT)
    total_author = Column(SMALLINT, nullable=False)
    open_access = Column(
        BOOLEAN(create_constraint=True, name='open_access_bool'),
        nullable=False
    )
    cited_cnt = Column(SMALLINT)
    url = Column(VARCHAR(256), nullable=False, unique=True)
    article_no = Column(VARCHAR(45))
    date = Column(DATE, nullable=False)
    fund_id = Column(BIGINT, ForeignKey('fund.id'))
    source_id = Column(INTEGER, ForeignKey('source.id'))
    doi = Column(VARCHAR(256), unique=True)
    volume = Column(VARCHAR(45))
    issue = Column(VARCHAR(45))
    page_range = Column(VARCHAR(45))
    retrieval_time = Column(DateTime(), nullable=False)
    create_time = Column(
        DateTime(), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    update_time = Column(
        DateTime(), nullable=False, server_default=text(UPDATE_TIME_DEFAULT))

    # Relationships
    fund = relationship('Fund', back_populates='papers')
    source = relationship('Source', back_populates='papers')
    keywords = relationship(
        'Keyword', secondary=Paper_Keyword, back_populates='papers')
    authors = relationship('Paper_Author', back_populates='paper')

    def __init__(
            self, *, id_scp: int, eid: str, title: str, type: str,
            type_description: str = None, abstract: str = None,
            total_author: int, open_access: bool, cited_cnt: int,
            url: str, article_no: str = None, date: date, fund_id: int = None,
            source_id: int = None, doi: str = None, volume: str = None,
            issue: str = None, page_range: str = None,
            retrieval_time: datetime,
            create_time: datetime = None, update_time: datetime = None,
    ) -> None:
        self.id_scp = id_scp
        self.eid = eid
        self.title = title
        self.type = type
        self.type_description = type_description
        self.abstract = abstract
        self.total_author = total_author
        self.open_access = open_access
        self.cited_cnt = cited_cnt
        self.url = url
        self.article_no = article_no
        self.fund_id = fund_id
        self.source_id = source_id
        self.doi = doi
        self.volume = volume
        self.issue = issue
        self.date = date
        self.page_range = page_range
        self.retrieval_time = retrieval_time
        self.create_time = create_time
        self.update_time = update_time

    def __repr__(self) -> str:
        max_len = 50
        if len(self.title) <= max_len:
            return f'{self.id_scp}: {self.title}; DOI: {self.doi}'
        return f'{self.id_scp}: {self.title[:max_len-3]}...; DOI: {self.doi}'

    def get_year(self) -> int:
        return self.date.year


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

        CREATE TRIGGER paper_update_time
            BEFORE UPDATE ON paper
            FOR EACH ROW
            EXECUTE PROCEDURE  set_update_time();
        '''
    )

    event.listen(Paper.__table__, 'after_create', update_time_trigger)
