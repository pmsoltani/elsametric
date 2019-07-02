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

papers = session.query(Paper) \
    .filter() .filter(
        extract('year',  Paper.date) >= 2011,
        extract('year',  Paper.date) <= 2018,
    ) \
    .all()
print(len(papers))
cnt = 0
iran_p = []
for paper in papers:
    if paper.source:
        if paper.source.country:
            if paper.source.country.domain == 'IR':
                ls = [paper.id, paper.title, paper.source.title, paper.source.publisher]
                print(ls)
                iran_p.append(ls)
                cnt += 1
print(f'{cnt}, {round(100 * cnt / len(papers), 2)}%')
