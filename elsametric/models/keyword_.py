from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import BIGINT, VARCHAR

from .base import Base
from .associations import Paper_Keyword


class Keyword(Base):
    __tablename__ = 'keyword'

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    keyword = Column(VARCHAR(256), nullable=False, unique=True)

    # Relationships
    papers = relationship(
        'Paper', secondary=Paper_Keyword, back_populates='keywords')

    def __init__(self, keyword: str) -> None:
        self.keyword = keyword

    def __repr__(self) -> str:
        return self.keyword
