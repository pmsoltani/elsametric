# from sqlalchemy import Column, ForeignKey
# from sqlalchemy.orm import relationship
# from sqlalchemy.dialects.mysql import BIGINT, INTEGER, VARCHAR

# from .base import Base


# class Institution_Alias(Base):
#     __tablename__ = 'institution_alias'

#     id = Column(
#         INTEGER(unsigned=True),
#         primary_key=True, autoincrement=True, nullable=False
#     )
#     institution_id = Column(
#         INTEGER(unsigned=True), ForeignKey('institution.id'), primary_key=True)
#     id_scp = Column(BIGINT(unsigned=True), nullable=False, unique=True)
#     alias = Column(VARCHAR(128), nullable=False)
#     url = Column(VARCHAR(256), nullable=True, unique=True)

#     # Relationships
#     institution = relationship('Institution', back_populates='aliases')

#     def __init__(self, id_scp, alias, institution_id=None, url=None):
#         self.institution_id = institution_id
#         self.id_scp = id_scp
#         self.alias = alias
#         self.url = url
