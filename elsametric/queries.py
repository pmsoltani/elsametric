from sqlalchemy import extract
from db_classes.base import Session

from db_classes.author import Author
from db_classes.author_profile import Author_Profile
from db_classes.country import Country
from db_classes.department import Department
from db_classes.fund import Fund
from db_classes.institution import Institution
from db_classes.keyword_ import Keyword
from db_classes.paper import Paper
from db_classes.source import Source
from db_classes.source_metric import Source_Metric
from db_classes.subject import Subject

# ==============================================================================
# Queries
# ==============================================================================

session = Session()

authors = session.query(Author)
profiles = session.query(Author_Profile)
countries = session.query(Country)
departments = session.query(Department)
funds = session.query(Fund)
institutions = session.query(Institution)
keywords = session.query(Keyword)
papers = session.query(Paper)
sources = session.query(Source)
metrics = session.query(Source_Metric)
subjects = session.query(Subject)

# ==============================================================================
# Playground
# ==============================================================================

papers = session.query(Paper) \
    .filter(
        extract('year', Paper.date) >= 2011,
        extract('year', Paper.date) <= 2018,
        Paper.id_scp == 84881620249
    ).first()
papers = session.query(Paper).get(1)

sources1 = session.query(Source).join(Country) \
    .filter(Country.domain == 'IR') \
    .filter(Source.publisher.contains('Sharif')) \
    .all()

p = session.query(Paper).filter(Paper.fund != None).first()
print(p)
print(p.date, type(p.date))

print(p.authors)
# print(authors.get(1).papers)
