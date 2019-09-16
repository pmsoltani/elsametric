import time
import io
import csv

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
# Functions
# ==============================================================================


def authors_list():
    authors = a \
        .with_entities(Author.id_frontend, Author.first, Author.last) \
        .join((Department, Author.departments)) \
        .join((Institution, Department.institution)) \
        .filter(Author.type == 'Faculty', Institution.id_scp == 60027666) \
        .order_by(Author.last) \
        .all()

    response = []
    for author in authors:
        response.append({
            'idFrontend': author.id_frontend,
            'first': author.first,
            'last': author.last,
            'url': f'http://localhost:8000/a/{author.id_frontend}'
        })
    return response


def author_id_frontend(id_: str):
    author = a.filter(Author.id_frontend == id_).first()
    departments = [{'name': d.name, 'idFrontend': d.id_frontend}
                   for d in author.departments]
    institutions = [{'name': i.name, 'idFrontend': i.id_frontend}
                    for i in author.get_institutions()]
    profiles = [{'type': p.type, 'address': p.address}
                for p in author.profiles]
    response = {
        'home': 'http://localhost:8000/a/list',
        'first': author.first,
        'last': author.last,
        'departments': departments,
        'institutions': institutions,
        'contact': profiles,
    }
    return response


if __name__ == "__main__":
    print(len(authors_list()))
    print(get_home_institution('id_scp', 60027666))
    print(authors_list())
