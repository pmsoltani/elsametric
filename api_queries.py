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
    response = {'message': 'author not found', 'code': 404}
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


if __name__ == "__main__":
    pass
