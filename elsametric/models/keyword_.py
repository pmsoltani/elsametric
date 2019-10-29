from sqlalchemy import CheckConstraint, Column
from sqlalchemy.orm import relationship
from sqlalchemy.types import BIGINT, VARCHAR

from .base import Base, DIALECT
from .associations import Paper_Keyword


class Keyword(Base):
    __tablename__ = 'keyword'
    __table_args__ = (
        CheckConstraint(
            'id >= 0',
            name='keyword_id_unsigned'
        ) if DIALECT == "postgresql" else None,
    )

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    keyword = Column(VARCHAR(256), nullable=False, unique=True)

    # Relationships
    papers = relationship(
        'Paper', secondary=Paper_Keyword, back_populates='keywords')

    def __init__(self, keyword: str) -> None:
        self.keyword = keyword

    def __repr__(self) -> str:
        return self.keyword
