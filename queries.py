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

# p = session.query(Paper, Author, Department, Institution) \
#     .filter(
#             Paper.id == Paper_Author.paper_id,
#             Paper_Author.author_id == Author.id) \
#     .filter(Author.id_scp == 6602882167) \
#     .all()

p = papers \
    .join((Paper_Author, Paper.authors)) \
    .join((Author, Paper_Author.author)) \
    .join((Department, Author.departments)) \
    .join((Institution, Department.institution)) \
    .filter(Institution.id_scp == 60010312).all()
    # .filter(Institution.name.contains('Iran Polymer')).all()

countries = {'unknown': 0}
paper_types = {'unknown': 0}
percentiles = {}
ippi = 0
count = 0
for cnt, paper in enumerate(p):
    year = int(str(paper.date).split('-')[0])
    if year != 2018:
        continue
    try:
        metrics = paper.source.metrics
        percentile = next(
            filter(
                lambda x: x.year == year and x.type == 'Percentile', metrics),
            None)
        percentiles[int(percentile.value)] += 1
    except AttributeError:
        continue
    except KeyError:
        percentiles[int(percentile.value)] = 1

    try:
        name = paper.source.country.name
        countries[name] += 1
    except AttributeError:
        countries['unknown'] += 1
    except KeyError:
        countries[name] = 1

    try:
        paper_type = paper.source.type
        paper_types[paper_type] += 1
    except AttributeError:
        print(paper.source)
        paper_types['unknown'] += 1
    except KeyError:
        paper_types[paper_type] = 1

    try:
        if paper.source.id_scp == 96087:
            ippi += 0
    except:
        pass

# print(ippi)
# # print()
# # print(paper_types)
# file_name = 'results2.txt'
# with io.open(file_name, 'w', encoding='utf-8') as output:
#     for country, count in percentiles.items():
#         output.write(f'{country}\t{count}\n')

print(countries)