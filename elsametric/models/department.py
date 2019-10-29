from datetime import datetime
from typing import Mapping, Set

from sqlalchemy import CheckConstraint, Column, DDL, event, ForeignKey, text
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime, DECIMAL, INTEGER, VARCHAR

from .base import (
    Base,
    DIALECT,
    token_generator,
    UPDATE_TIME_DEFAULT,
    VARCHAR_COLUMN_LENGTH
)
from .author import Author
from .associations import Author_Department
from .source import Source
from .subject import Subject


class Department(Base):
    __tablename__ = 'department'
    __table_args__ = (
        CheckConstraint(
            'id >= 0',
            name='department_id_unsigned'
        ) if DIALECT == "postgresql" else None,
    )

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    institution_id = Column(
        INTEGER, ForeignKey('institution.id'), primary_key=True)
    id_frontend = Column(
        VARCHAR(VARCHAR_COLUMN_LENGTH), nullable=False, unique=True)
    name = Column(VARCHAR(128), nullable=False)
    name_fa = Column(VARCHAR(128))
    abbreviation = Column(VARCHAR(45))
    url = Column(VARCHAR(256), unique=True)
    type = Column(VARCHAR(45))
    lat = Column(DECIMAL(8, 6))
    lng = Column(DECIMAL(9, 6))
    create_time = Column(
        DateTime(), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    update_time = Column(
        DateTime(), nullable=False, server_default=text(UPDATE_TIME_DEFAULT))

    # Relationships
    institution = relationship('Institution', back_populates='departments')
    # aliases = relationship('Department_Alias', back_populates='department')
    authors = relationship(
        'Author', secondary=Author_Department, back_populates='departments')

    def __init__(
            self, name: str, name_fa: str = None, institution_id: int = None,
            abbreviation: str = None, url: str = None, type: str = None,
            lat: float = None, lng: float = None,
            create_time: datetime = None, update_time: datetime = None
    ) -> None:
        self.institution_id = institution_id
        self.id_frontend = token_generator()
        self.name = name
        self.abbreviation = abbreviation
        self.type = type
        self.lat = lat
        self.lng = lng
        self.create_time = create_time
        self.update_time = update_time

    def __repr__(self) -> str:
        max_len = 50
        if len(self.name) <= max_len:
            return f'{self.name} @ {self.institution}'
        return f'{self.name[:max_len-3]}... @ {self.institution}'

    def get_papers_trend(self) -> Mapping[int, int]:
        self._papers = {}
        for author in self.authors:
            for paper_author in author.papers:
                try:
                    year = paper_author.paper.get_year()
                    self._papers[year] += 1
                except KeyError:
                    self._papers[year] = 1
        self.total_papers = sum(self._papers.values())
        return self._papers

    def get_citations_trend(self) -> Mapping[int, int]:
        self._citations = {}
        for author in self.authors:
            for paper_author in author.papers:
                try:
                    year = paper_author.paper.get_year()
                    citations = paper_author.paper.cited_cnt
                    if not citations:
                        citations = 0
                    self._citations[year] += citations
                except KeyError:
                    self._citations[year] = citations
        self.total_citations = sum(self._citations.values())
        return self._citations

    def get_sources(self) -> Set[Source]:
        self._sources = set()
        for author in self.authors:
            for paper_author in author.papers:
                try:
                    self._sources.add(paper_author.paper.source)
                except AttributeError:
                    continue

        self.total_sources = len(self._sources)
        return self._sources

    def get_metrics(self, histogram: bool = False) -> list:
        self._metrics = [[i, 0] for i in range(100)]
        for author in self.authors:
            for paper_author in author.papers:
                paper = paper_author.paper
                year = paper.get_year()
                percentile = None
                try:
                    for met in paper.source.metrics:
                        if met.type == 'Percentile' and met.year == year:
                            percentile = int(met.value)
                            break
                    if percentile:
                        self._metrics[percentile][1] += 1
                except AttributeError:
                    # paper doesn't have a source, or its source any metrics
                    continue

        if histogram:
            result = []
            for met in self._metrics:
                result.extend([met[0] for percentile in range(met[1])])
            return result
        return self._metrics

    def get_co_authors(self, threshold: int = 0) -> Mapping[Author, int]:
        self._co_authors = {}
        for author in self.authors:
            for paper_author_1 in author.papers:
                paper = paper_author_1.paper
                for paper_author_2 in paper.authors:
                    auth = paper_author_2.author
                    if auth in self.authors:
                        continue
                    try:
                        self._co_authors[auth] += 1
                    except KeyError:
                        self._co_authors[auth] = 1

        if threshold:
            self._co_authors = {
                k: v for k, v in self._co_authors.items() if threshold <= v}

        return self._co_authors

    def get_subjects(self) -> Mapping[Subject, int]:
        self._subjects = {}
        for author in self.authors:
            for paper_author in author.papers:
                try:
                    subjects = paper_author.paper.source.subjects
                    for subject in subjects:
                        try:
                            self._subjects[subject] += 1
                        except KeyError:
                            self._subjects[subject] = 1
                except AttributeError:
                    # paper's source doesn't have any subjects registered
                    continue

        return self._subjects

    def get_keywords(self, threshold: int = 0) -> Mapping[str, int]:
        self._keywords = {}
        for author in self.authors:
            for paper_author in author.papers:
                try:
                    keywords = paper_author.paper.keywords
                    for keyword in keywords:
                        try:
                            self._keywords[keyword.keyword] += 1
                        except KeyError:
                            self._keywords[keyword.keyword] = 1
                except AttributeError:
                    # paper doesn't have any keywords registered
                    continue

        if threshold:
            self._keywords = {
                k: v for k, v in self._keywords.items() if threshold <= v}

        return self._keywords

    def get_funds(self) -> Mapping[str, int]:
        self._funds = {'unknown': 0}
        for author in self.authors:
            for paper_author in author.papers:
                try:
                    agency = paper_author.paper.fund.agency
                    if agency == 'NOT AVAILABLE':
                        agency = 'unknown'
                    try:
                        self._funds[agency] += 1
                    except KeyError:
                        self._funds[agency] = 1
                except AttributeError:
                    # paper doesn't have any funds registered
                    continue

        return self._funds


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

        CREATE TRIGGER department_update_time
            BEFORE UPDATE ON department
            FOR EACH ROW
            EXECUTE PROCEDURE  set_update_time();
        '''
    )

    event.listen(Department.__table__, 'after_create', update_time_trigger)
