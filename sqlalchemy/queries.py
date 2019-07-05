from sqlalchemy import extract
from base import Session, engine, Base

# from functions import key_get, strip, country_names
from keyword_ import Keyword
from source import Source
from source_metric import Source_Metric
from fund import Fund
from author import Author
from author_profile import Author_Profile
from institution import Institution
from department import Department
from country import Country
from subject import Subject
from paper import Paper

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


print('-----')
print(len(sources1), type(sources1))
print(sources1[0].id_scp, sources1[0].title)
print()
# for s in range(12, 20):
#     print(f'{sources1[s].id_scp}\t {sources1[s].title}')
#     print(f'{sources2[s].id_scp}\t {sources2[s].title}')
#     print()

papers1 = session.query(Paper) \
    .with_parent(sources1[0], Source.papers) \
    .filter(extract('year',  Paper.date) == 2015) \
    .all()

print(type(session))
print(type(papers), len(papers))
print(papers[0].id_scp, papers[0].title, papers[0].source.title)
