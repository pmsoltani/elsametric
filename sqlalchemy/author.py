from sqlalchemy import Column, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import \
    BIGINT, CHAR, DATETIME, ENUM, INTEGER, VARCHAR

from base import Base
from associations import Paper_Author, Author_Department

class Author(Base):
    __tablename__ = 'author'

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    id_scp = Column(BIGINT(unsigned=True), nullable=False, unique=True)
    first = Column(VARCHAR(45), nullable=True)
    middle = Column(VARCHAR(45), nullable=True)
    last = Column(VARCHAR(45), nullable=True)
    initials = Column(VARCHAR(45), nullable=True)
    sex = Column(
        CHAR(1), ENUM('m', 'f'),
        nullable=True
    )
    type = Column(VARCHAR(45), nullable=True)
    rank = Column(VARCHAR(45), nullable=True)
    create_time = Column(
        DATETIME(), nullable=False,
        server_default=text('CURRENT_TIMESTAMP')
    )
    update_time = Column(
        DATETIME(), nullable=False,
        server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    )

    # Relationships
    papers = relationship('Paper_Author', back_populates='author')
    profiles = relationship('Author_Profile', back_populates='author')
    departments = relationship(
        'Department', secondary=Author_Department, foreign_keys=['author_department.department_id', 'author_department.institution_id'], back_populates='authors')
    
    def __init__(
        self, id_scp, first=None, middle=None, last=None, initials=None, 
        sex=None, type=None, rank=None, create_time=None, update_time=None
    ):
        self.id_scp = id_scp
        self.first = first
        self.middle = middle
        self.last = last
        self.initials = initials
        self.sex = sex
        self.type = type
        self.rank = rank
        self.create_time = create_time
        self.update_time = update_time