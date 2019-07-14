from sqlalchemy import extract
from elsametric.db_classes.base import Session, engine, Base

from elsametric.db_classes.keyword_ import Keyword
from elsametric.db_classes.source import Source
from elsametric.db_classes.source_metric import Source_Metric
from elsametric.db_classes.fund import Fund
from elsametric.db_classes.author import Author
from elsametric.db_classes.author_profile import Author_Profile
from elsametric.db_classes.institution import Institution
from elsametric.db_classes.department import Department
from elsametric.db_classes.country import Country
from elsametric.db_classes.subject import Subject
from elsametric.db_classes.paper import Paper

session = Session()

# papers = session.query(Paper) \
#     .filter() .filter(
#         extract('year',  Paper.date) >= 2011,
#         extract('year',  Paper.date) <= 2018,
#     ) \
#     .all()
# print(len(papers))
# cnt = 0
# iran_p = []
# for paper in papers:
#     if paper.source:
#         if paper.source.country:
#             if paper.source.country.domain == 'IR':
#                 ls = [paper.id, paper.title,
#                       paper.source.title, paper.source.publisher]
#                 # print(ls)
#                 iran_p.append(ls)
#                 cnt += 1
# print(f'{cnt}, {round(100 * cnt / len(papers), 2)}%')

# foreign = []
# for p in papers:
#     for pa in p.authors:
#         if not pa.author.departments:
#             continue
#         if all('Sharif' not in d.institution.name for d in pa.author.departments):
#             foreign.append(p)
#             break
# print(
#     f'Papers with foreign authors: {len(foreign)} ({round(100 * len(foreign) / len(papers), 2)}%)')

# ==============================================================================
# Playground
# ==============================================================================

papers = session.query(Paper) \
    .filter(
        extract('year',  Paper.date) >= 2011,
        extract('year',  Paper.date) <= 2018,
        Paper.id_scp == 84881620249
    ).first()
papers = session.query(Paper).get(1)

sources1 = session.query(Source).join(Country) \
    .filter(Country.domain == 'IR') \
    .filter(Source.publisher.contains('Sharif')) \
    .all()

p = session.query(Paper).first()
print(p.eid, p.id_scp)
