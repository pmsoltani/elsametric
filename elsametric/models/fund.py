from sqlalchemy import CheckConstraint, Column, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.types import BIGINT, VARCHAR

from .base import Base


class Fund(Base):
    __tablename__ = 'fund'
    __table_args__ = (
        CheckConstraint(
            'NOT(id_scp IS NULL AND agency IS NULL)',
            name='ck_fund_idscp_agency'
        ),
        # CheckConstraint('id >= 0', name='fund_id_unsigned'),
        UniqueConstraint('id_scp', 'agency', name='uq_fund_idscp_agency'),
    )

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    id_scp = Column(VARCHAR(256))
    agency = Column(VARCHAR(256))
    agency_acronym = Column(VARCHAR(256))

    # Relationships
    papers = relationship('Paper', back_populates='fund')

    def __init__(self, id_scp: str = None,
                 agency: str = None, agency_acronym: str = None) -> None:
        self.id_scp = id_scp
        self.agency = agency
        self.agency_acronym = agency_acronym

    def __repr__(self) -> str:
        if not self.agency_acronym:
            return f'{self.id_scp} by {self.agency}'
        return f'{self.id_scp} by {self.agency} ({self.agency_acronym})'
