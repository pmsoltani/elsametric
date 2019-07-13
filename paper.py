from sqlalchemy import Column, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import \
    BIGINT, BOOLEAN, DATE, DATETIME, INTEGER, SMALLINT, TEXT, VARCHAR

from base import Base
from associations import Paper_Keyword, Paper_Author

class Paper(Base):
    __tablename__ = 'paper'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    id_scp = Column(BIGINT(unsigned=True), nullable=False, unique=True)
    eid = Column(VARCHAR(45), nullable=False, unique=True)
    title = Column(VARCHAR(512), nullable=False)
    type = Column(VARCHAR(2), nullable=False)
    type_description = Column(VARCHAR(45), nullable=True)
    abstract = Column(TEXT(), nullable=True)
    total_author = Column(SMALLINT(unsigned=True), nullable=False)
    open_access = Column(
        BOOLEAN(create_constraint=True, name='open_access_check'), 
        nullable=False
    )
    cited_cnt = Column(SMALLINT(unsigned=True), nullable=True)
    url = Column(VARCHAR(256), nullable=False, unique=True)
    article_no = Column(VARCHAR(45), nullable=True)
    date = Column(DATE(), nullable=False)
    fund_id = Column(
        BIGINT(unsigned=True), ForeignKey('fund.id'), nullable=True)
    source_id = Column(
        INTEGER(unsigned=True), ForeignKey('source.id'), nullable=True)
    doi = Column(VARCHAR(256), nullable=True, unique=True)
    volume = Column(VARCHAR(45), nullable=True)
    issue = Column(VARCHAR(45), nullable=True)
    page_range = Column(VARCHAR(45), nullable=True)
    retrieval_time = Column(DATETIME(), nullable=False)
    create_time = Column(
        DATETIME(), nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    update_time = Column(
        DATETIME(), nullable=False,
        server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    )

    # Relationships
    fund = relationship('Fund', back_populates='papers')
    source = relationship('Source', back_populates='papers')
    keywords = relationship(
        'Keyword', secondary=Paper_Keyword, back_populates='papers')
    authors = relationship('Paper_Author', back_populates='paper')
    
    def __init__(
        self, id_scp, eid, title, type, total_author, open_access, cited_cnt, 
        url, date, retrieval_time, type_description=None, abstract=None, 
        article_no=None, fund_id=None, source_id=None, doi=None, volume=None, 
        issue=None, page_range=None, create_time=None, update_time=None, 
    ):
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