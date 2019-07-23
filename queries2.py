import time
import io
import csv

from sqlalchemy import extract
from elsametric.db_classes.base import Session

from elsametric.db_classes.associations import Author_Department
from elsametric.db_classes.associations import Paper_Keyword
from elsametric.db_classes.associations import Paper_Author
from elsametric.db_classes.associations import Source_Subject

from elsametric.db_classes.author import Author
from elsametric.db_classes.author_profile import Author_Profile
from elsametric.db_classes.country import Country
from elsametric.db_classes.department import Department
from elsametric.db_classes.fund import Fund
from elsametric.db_classes.institution import Institution
from elsametric.db_classes.keyword_ import Keyword
from elsametric.db_classes.paper import Paper
from elsametric.db_classes.source import Source
from elsametric.db_classes.source_metric import Source_Metric
from elsametric.db_classes.subject import Subject

# ==============================================================================
# Queries
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

t0 = time.time()

# ==============================================================================
# Playground
# ==============================================================================

department = d.filter(Department.abbreviation == 'ChE').first()

print(department.get_metrics(histogram=True))
# print(department.total_papers)
print()


# ==============================================================================
# Ending
# ==============================================================================

print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')
