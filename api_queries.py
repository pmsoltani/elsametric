import os
import json

from sqlalchemy import extract
from sqlalchemy.orm import aliased

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
network_threshold = config['network_threshold']


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


home_institution = i.filter(
    Institution.id_scp == home_institution_id_scp).first()


def get_authors_list():
    authors = a \
        .with_entities(
            Author.id, Author.id_frontend, Author.first, Author.last) \
        .distinct() \
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
    percentile = None
    quartile = None
    if paper.source and paper.source.metrics:
        percentile = next(filter(
            lambda m: m.type == 'Percentile' and m.year == paper.get_year(),
            paper.source.metrics
        ), None)
    if percentile:
        percentile = percentile.value
        quartile = f'q{(100 - percentile - 1) // 25 + 1}'

    return {
        'title': paper.title,
        'type': paper.type,
        'date': paper.get_year(),
        'doi': paper.doi,
        'open_access': paper.open_access,
        'cited_cnt': paper.cited_cnt,
        'source': paper.source.title,
        'quartile': quartile
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


def get_author_journals(id_frontend: str, q: str = ''):
    response = {'message': 'not found', 'code': 404}

    if not(isinstance(q, str)):
        return response

    if q and (q not in ['q1', 'q2', 'q3', 'q4']):
        return response

    try:
        id_ = authors_list_backend[id_frontend]
        author = a.get(id_)
        metrics = {'q1': 0, 'q2': 0, 'q3': 0, 'q4': 0}

        if author:
            try:
                if q:
                    quartile = int(q[1])
                    top_percentile = (4 - quartile) * 25 + 25 - 1
                    bottom_percentile = (4 - quartile) * 25
                    papers = p \
                        .join((Paper_Author, Paper.authors)) \
                        .join((Author, Paper_Author.author)) \
                        .filter(Author.id == id_) \
                        .all()

                    papers2 = []
                    for paper in papers:
                        if paper.source and paper.source.metrics:
                            for metric in paper.source.metrics:
                                if (
                                    metric.year == paper.get_year() and
                                    metric.type == 'Percentile' and
                                    bottom_percentile <= metric.value and
                                    metric.value <= top_percentile
                                ):
                                    papers2.append(paper_formatter(paper))
                    response = papers2
                else:
                    for i in author.get_metrics():
                        quartile = (100 - i[0] - 1) // 25 + 1
                        metrics[f'q{quartile}'] += i[1]

                    response = metrics

            except AttributeError as e:
                print('attr', e)
                pass
    except KeyError as e:
        print('key', e)
        pass

    return response


def get_joint_papers(all_papers: list, co_author):
    joint_papers = []
    for paper in all_papers:
        authors = [paper_author.author for paper_author in paper.authors]
        if co_author in authors:
            joint_papers.append(paper)

    return joint_papers


def network_formatter(from_, to_dict: dict):
    result = []
    for k, v in to_dict.items():
        result.append({
            'from': {
                'name': f'{from_.first} {from_.last}',
                'idFrontend': from_.id_frontend,
            },
            'to': {
                'name': f'{k.first} {k.last}',
                'idFrontend': k.id_frontend
            },
            'value': v,
            'url': f'http://localhost:8000/a/{from_.id_frontend}/network?coID={k.id_frontend}'
        })

    return result


def get_author_network(id_frontend: str):
    response = {'message': 'not found', 'code': 404}
    final_network = []

    # 1. get a list of (author)'s (all_papers)
    id_ = authors_list_backend[id_frontend]
    author = a.get(id_)
    all_papers = p \
        .join((Paper_Author, Paper.authors)) \
        .join((Author, Paper_Author.author)) \
        .filter(Author.id == id_) \
        .all()

    # 2. add (author) to an (exclusion_list)
    exclusion_list = [author]

    # 3. get a list of (author)'s all (co_authors)
    co_authors = author.get_co_authors(threshold=network_threshold)
    final_network.extend(network_formatter(author, co_authors))

    # 4. create a dictionary for storing each the (co_authors) of each (co)
    co_network = {}

    # 5. for each (co):
    for co in co_authors:

        # 5.1. add (co) to (exclusion_list) and prepare (co_network)
        exclusion_list.append(co)
        co_network[co] = {}

        # 5.2. get a list of (joint_papers) with (author)
        joint_papers = get_joint_papers(all_papers, co_author=co)

        # 5.3. for each (paper) in (joint_papers)
        for paper in joint_papers:

            # 5.3.1. get a list of joint paper's (authors)
            authors = [paper_author.author for paper_author in paper.authors]

            # 5.3.2 add (authors) to the (co_network) for (co)
            for auth in authors:
                if auth in exclusion_list:
                    continue

                try:
                    co_network[co][auth] += 1
                except KeyError as e:
                    co_network[co][auth] = 1

        # 5.4 prune the (co_network) according to (network_threshold)
        co_network[co] = {k: v for k, v in co_network[co].items()
                          if v >= network_threshold}

    for co, network in co_network.items():
        final_network.extend(network_formatter(co, network))

    response = final_network

    return response


def get_joint_papers_id(id_frontend: str, co_id: str):
    response = {'message': 'not found', 'code': 404}

    if not(isinstance(co_id, str)):
        return response

    co_author = a.filter(Author.id_frontend == co_id).first()
    if not co_author:
        return response

    try:
        id_ = authors_list_backend[id_frontend]
        author = a.get(id_)

        if author:
            all_papers = p \
                .join((Paper_Author, Paper.authors)) \
                .join((Author, Paper_Author.author)) \
                .filter(Author.id == id_) \
                .all()

            joint_papers = []
            for paper in all_papers:
                authors = [
                    paper_author.author for paper_author in paper.authors]

                if co_author in authors:
                    joint_papers.append(paper_formatter(paper))

            response = joint_papers
    except (KeyError, AttributeError) as e:
        pass

    return response


if __name__ == "__main__":
    print()
