from sqlalchemy import Column, CheckConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import \
    BIGINT, CHAR, DATETIME, ENUM, INTEGER, VARCHAR

from .base import Base, token_generator
from .associations import Author_Department, Paper_Author


class Author(Base):
    __tablename__ = 'author'
    __table_args__ = (
        CheckConstraint(
            '''NOT(
                (NOT(h_index_gsc IS NULL) OR NOT(i10_index_gsc IS NULL)) AND
                (retrieval_time_gsc IS NULL)
            )''',
            name='ck_author_google_scholar'
        )
    )

    id = Column(
        INTEGER(unsigned=True),
        primary_key=True, autoincrement=True, nullable=False
    )
    id_scp = Column(BIGINT(unsigned=True), nullable=False, unique=True)
    id_gsc = Column(VARCHAR(12), nullable=True, unique=True)
    id_institution = Column(VARCHAR(45), nullable=True)
    id_frontend = Column(VARCHAR(11), nullable=False, unique=True)
    first = Column(VARCHAR(45), nullable=True)
    middle = Column(VARCHAR(45), nullable=True)
    last = Column(VARCHAR(45), nullable=True)
    initials = Column(VARCHAR(45), nullable=True)
    first_pref = Column(VARCHAR(45), nullable=True)
    middle_pref = Column(VARCHAR(45), nullable=True)
    last_pref = Column(VARCHAR(45), nullable=True)
    initials_pref = Column(VARCHAR(45), nullable=True)
    first_fa = Column(VARCHAR(45), nullable=True)
    last_fa = Column(VARCHAR(45), nullable=True)
    sex = Column(CHAR(1), ENUM('m', 'f'), nullable=True)
    type = Column(VARCHAR(45), nullable=True)
    rank = Column(VARCHAR(45), nullable=True)
    h_index_gsc = Column(INTEGER(unsigned=True), nullable=True)
    i10_index_gsc = Column(INTEGER(unsigned=True), nullable=True)
    retrieval_time_gsc = Column(DATETIME(), nullable=True)
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
        'Department', secondary=Author_Department, back_populates='authors')

    def __init__(
        self, id_scp, id_gsc=None, id_institution=None, first=None, middle=None,
        last=None, initials=None, first_pref=None, middle_pref=None,
        last_pref=None, initials_pref=None, first_fa=None, last_fa=None,
        sex=None, type=None, rank=None, h_index_gsc=None, i10_index_gsc=None,
        retrieval_time_gsc=None, create_time=None, update_time=None):

        self.id_scp = id_scp
        self.id_gsc = id_gsc
        self.id_institution = id_institution
        self.id_frontend = token_generator()
        self.first = first
        self.middle = middle
        self.last = last
        self.initials = initials
        self.first_pref = first
        self.middle_pref = middle
        self.last_pref = last
        self.initials_pref = initials
        self.first_fa = first_fa
        self.last_fa = last_fa
        self.sex = sex
        self.type = type
        self.rank = rank
        self.h_index_gsc = h_index_gsc
        self.i10_index_gsc = i10_index_gsc
        self.retrieval_time_gsc = retrieval_time_gsc
        self.create_time = create_time
        self.update_time = update_time
        self._institutions = set()
        self._countries = set()

    def __repr__(self):
        return f'{self.id_scp}: {self.first} {self.last}'

    def get_institutions(self):
        self._institutions = set()
        for department in self.departments:
            try:
                self._institutions.add(department.institution)
            except AttributeError:
                continue

        self.total_institutions = len(self._institutions)
        return self._institutions

    def get_countries(self):
        self._countries = set()
        for institution in self.get_institutions():
            try:
                self._countries.add(institution.country)
            except AttributeError:
                continue

        self.total_countries = len(self._countries)
        return self._countries

    def get_papers(self):
        self._papers = {}
        for paper_author in self.papers:
            try:
                year = paper_author.paper.get_year()
                self._papers[year] += 1
            except KeyError:
                self._papers[year] = 1

        return self._papers

    def get_citations(self):
        self._citations = {}
        for paper_author in self.papers:
            try:
                paper = paper_author.paper
                year = paper.get_year()
                citations = paper.cited_cnt
                if not citations:
                    citations = 0
                self._citations[year] += citations
            except KeyError:
                self._citations[year] = citations

        return self._citations

    def get_sources(self):
        self._sources = set()
        for paper_author in self.papers:
            try:
                self._sources.add(paper_author.paper.source)
            except AttributeError:
                continue

        self.total_sources = len(self._sources)
        return self._sources

    def get_metrics(self, histogram=False):
        self._metrics = [[i, 0] for i in range(100)]
        self._metrics.append(['Undefined', 0])
        for paper_author in self.papers:
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
                else:
                    self._metrics[-1][1] += 1
            except AttributeError:
                # either paper doesn't have a source, or its source any metric
                continue

        if histogram:
            result = []
            for met in self._metrics:
                result.extend([met[0] for percentile in range(met[1])])
            return result
        return self._metrics

    def get_co_authors(self, threshold: int = 0):
        self._co_authors = {}
        for paper_author_1 in self.papers:
            paper = paper_author_1.paper
            for paper_author_2 in paper.authors:
                author = paper_author_2.author
                if author == self:
                    continue
                try:
                    self._co_authors[author] += 1
                except KeyError:
                    self._co_authors[author] = 1

        if threshold:
            self._co_authors = {
                k: v for k, v in self._co_authors.items() if threshold <= v}

        return self._co_authors

    def get_subjects(self):
        self._subjects = {}
        for paper_author in self.papers:
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

    def get_keywords(self, text: bool = False, threshold: int = 0):
        self._keywords = {}
        for paper_author in self.papers:
            try:
                keywords = paper_author.paper.keywords
                for keyword in keywords:
                    try:
                        # 'keyword.keyword' is the str value of keyword object
                        self._keywords[keyword.keyword] += 1
                    except KeyError:
                        self._keywords[keyword.keyword] = 1
            except AttributeError:
                # paper doesn't have any keywords registered
                continue

        if threshold:
            self._keywords = {
                k: v for k, v in self._keywords.items() if threshold <= v}

        if text:
            result = []
            for k, v in self._keywords.items():
                result.append((str(k) + ' ') * v)
            return ' '.join(result)
        return self._keywords

    def get_funds(self):
        self._funds = {'unknown': 0}
        for paper_author in self.papers:
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
