import os
import json

from sqlalchemy import extract

from elsametric.models.base import Session
from elsametric.models.associations import Author_Department
from elsametric.models.associations import Paper_Keyword
from elsametric.models.associations import Paper_Author
from elsametric.models.associations import Source_Subject
from elsametric.models.author import Author
from elsametric.models.author_profile import Author_Profile
from elsametric.models.country import Country
from elsametric.models.department import Department
from elsametric.models.fund import Fund
from elsametric.models.institution import Institution
from elsametric.models.keyword_ import Keyword
from elsametric.models.paper import Paper
from elsametric.models.source import Source
from elsametric.models.source_metric import Source_Metric
from elsametric.models.subject import Subject


# ==============================================================================
# Config
# ==============================================================================


config_path = os.path.join(os.getcwd(), 'config.json')
with open(config_path, 'r') as config_file:
    config = json.load(config_file)

config = config['api']
home_institution_id_scp = config['home_institution_id_scp']
year_range = config['year_range']
keywords_threshold = config['keywords_threshold']


# ==============================================================================
# Queries: Base
# ==============================================================================


session = Session()

a = session.query(Author)
prf = session.query(Author_Profile)
c = session.query(Country)
d = session.query(Department)
f = session.query(Fund)
i = session.query(Institution)
k = session.query(Keyword)
p = session.query(Paper)
src = session.query(Source)
m = session.query(Source_Metric)
sub = session.query(Subject)


# ==============================================================================
# Functions & Variables
# ==============================================================================


def get_authors_list():
    authors = a \
        .with_entities(
            Author.id, Author.id_frontend, Author.first, Author.last) \
        .join((Department, Author.departments)) \
        .join((Institution, Department.institution)) \
        .filter(
            Author.type == 'Faculty',
            Institution.id_scp == home_institution_id_scp) \
        .order_by(Author.last) \
        .all()

    response_backend = {}
    response_frontend = []
    for author in authors:
        response_backend[author.id_frontend] = author.id

        response_frontend.append({
            'idFrontend': author.id_frontend,
            'first': author.first,
            'last': author.last,
            'url': f'http://localhost:8000/a/{author.id_frontend}'
        })
    return response_backend, response_frontend


authors_list_backend, authors_list_frontend = get_authors_list()
home_institution = i.filter(
    Institution.id_scp == home_institution_id_scp).first()


def get_author(id_frontend: str):
    response = {'message': 'not found', 'code': 404}
    try:
        id_ = authors_list_backend[id_frontend]
        author = a.get(id_)
        departments = []
        profiles = []
        if author:
            try:
                for d in author.departments:
                    if d.name == 'Undefined':
                        continue
                    departments.append(
                        {'name': d.name, 'idFrontend': d.id_frontend})
            except (TypeError, AttributeError):
                pass

            try:
                for p in author.profiles:
                    profiles.append(
                        {'type': p.type, 'address': p.address})
            except (TypeError, AttributeError):
                pass

            response = {
                'home': 'http://localhost:8000/a/list',
                'first': author.first,
                'last': author.last,
                'departments': departments,
                'institution': {
                    'name': home_institution.name,
                    'idFrontend': home_institution.id_frontend
                },
                'contact': profiles,
            }
    except KeyError:
        pass

    return response


def paper_formatter(paper):
    return {
        'title': paper.title,
        'type': paper.type,
        'date': paper.get_year(),
        'doi': paper.doi,
        'open_access': paper.open_access,
        'cited_cnt': paper.cited_cnt,
        'source': paper.source.title
    }


def get_author_papers(id_frontend: str, year: int = 0):
    response = {'message': 'not found', 'code': 404}

    if not(isinstance(year, int)):
        return response

    if year and not(year_range[0] <= year <= year_range[1]):
        return response

    try:
        id_ = authors_list_backend[id_frontend]
        author = a.get(id_)
        papers = []

        if author:
            try:
                for paper_author in author.papers:
                    paper = paper_author.paper
                    if year and paper.get_year() != year:
                        continue
                    papers.append(paper_formatter(paper))
                response = papers

            except (AttributeError, TypeError):
                pass
    except KeyError:
        pass

    return response


def get_author_trend(id_frontend: str):
    response = {'message': 'not found', 'code': 404}
    try:
        id_ = authors_list_backend[id_frontend]
        author = a.get(id_)
        trend = {}

        if author:
            try:
                papers_trend = author.get_papers()
                citations_trend = author.get_citations()
                for year in papers_trend:
                    trend[year] = {
                        'papers': papers_trend[year],
                        'citations': citations_trend[year]
                    }
                response = trend

            except (AttributeError, TypeError):
                pass
    except KeyError:
        pass

    return response


def get_author_keywords(id_frontend: str, keyword: str = ''):
    response = {'message': 'not found', 'code': 404}

    if not(isinstance(keyword, str)):
        return response

    if keyword:
        keywords_list = get_author_keywords(id_frontend).keys()
        if keyword not in keywords_list:
            return response

    try:
        id_ = authors_list_backend[id_frontend]
        author = a.get(id_)
        keywords = {}

        if author:
            try:
                if keyword:
                    papers = p \
                        .join((Paper_Author, Paper.authors)) \
                        .join((Author, Paper_Author.author)) \
                        .join((Keyword, Paper.keywords)) \
                        .filter(Author.id == id_, Keyword.keyword == keyword) \
                        .all()
                    papers = [paper_formatter(p) for p in papers]
                    response = papers
                else:
                    keywords = author.get_keywords(
                        threshold=keywords_threshold)
                    response = {k.keyword: v for k, v in keywords.items()}

            except (AttributeError):
                pass
    except KeyError:
        pass

    return response


def get_author_journals(id_frontend: str, rank: str = ''):
    response = {'message': 'not found', 'code': 404}

    if not(isinstance(rank, str)):
        return response

    if rank and (rank not in ['q1', 'q2', 'q3', 'q4']):
        return response

    try:
        id_ = authors_list_backend[id_frontend]
        author = a.get(id_)
        metrics = {'q1': 0, 'q2': 0, 'q3': 0, 'q4': 0}

        if author:
            try:
                if rank:
                    print('@rank')
                    quartile = int(rank[1])
                    top_percentile = (4 - quartile) * 25 + 25 - 1
                    bottom_percentile = (4 - quartile) * 25
                    print(quartile, top_percentile, bottom_percentile)
                    papers = p \
                        .join((Paper_Author, Paper.authors)) \
                        .join((Author, Paper_Author.author)) \
                        .join((Source, Paper.source_id)) \
                        .join((Source_Metric, Source_Metric.source_id)) \
                        .filter(
                            Author.id == id_,
                            Source_Metric.type == 'percentile',
                            Source_Metric.value >= bottom_percentile,
                            Source_Metric.value <= top_percentile
                        ) \
                        .all()
                    papers = [paper_formatter(p) for p in papers]
                    response = papers
                else:
                    for i in author.get_metrics():
                        quartile = (100 - i[0] - 1) // 25 + 1
                        metrics[f'q{quartile}'] += i[1]

                    response = metrics

            except (AttributeError) as e:
                pass
    except KeyError as e:
        pass

    return response


def get_author_network(id_frontend: str):
    response = {'message': 'not found', 'code': 404}

    try:
        id_ = authors_list_backend[id_frontend]
        author = a.get(id_)
        network = []

        if author:
            try:
                for co_auth, value in author.get_co_authors().items():
                    network.append({
                        'from': f'{author.first} {author.last}',
                        'to': f'{co_auth.first} {co_auth.last}',
                        'value': value
                    })

                response = network

            except (AttributeError) as e:
                pass
    except KeyError as e:
        pass

    return response


if __name__ == "__main__":
    pass
