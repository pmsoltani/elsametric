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
        .join((Department, Author.departments)) \
        .join((Institution, Department.institution)) \
        .filter(Institution.id_scp == 60027666).all()
    return [{'id_frontend': i.id_frontend, 'first': i.first, 'last': i.last}
            for i in authors]
