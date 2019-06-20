from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR

from base import Base

class Department_Alias(Base):
    __tablename__ = 'department_alias'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    department_id = Column(
        INTEGER(unsigned=True), ForeignKey('department.id'), primary_key=True)
    institution_id = Column(
        INTEGER(unsigned=True), ForeignKey('institution.id'), primary_key=True)
    alias = Column(VARCHAR(128), nullable=False)
    
    # Relationships
    department = relationship('Department', back_populates='aliases')

    def __init__(self, alias, department_id=None, institution_id=None):
        self.department_id = department_id
        self.institution_id = institution_id
        self.alias = alias