import time

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

t0 = time.time()

p = papers.all()
cnt = 0
for paper in p:
    if paper.total_author != len(paper.authors) and paper.total_author != 100:
        print(paper, paper.total_author, len(paper.authors))
        cnt += 1
print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')

