from base import Session, engine, Base

from paper import Paper
from fund import Fund

Base.metadata.create_all(engine)
session = Session()

p1 = Paper(
    id_scp=1271,
    eid='s1271',
    title='Nanotechnology: A case study',
    type='ar',
    total_author=3,
    open_access=0,
    cited_cnt=2,
    url='www1',
    date='2019-02-03',
    retrieval_time='2019-06-06 12:12:12'
)
p2 = Paper(
    id_scp=1543,
    eid='s1543',
    title='Effect of X on Y',
    type='cp',
    total_author=1,
    open_access=1,
    cited_cnt=20,
    url='www2',
    date='2018-07-13',
    retrieval_time='2019-06-06 12:12:15'
)

f1 = Fund(
    id_scp='DE-AC05-00OR22725',
    agency='Oak Ridge National Laboratory',
    agency_acronym='ORNL'
)
f2 = Fund(
    id_scp='CE124-948',
    agency='Iran National Science Foundation',
    agency_acronym='INSF',
)

# p1.fund = f2
# print(p1.fund_id)

# session.add(p1)
# session.add(p2)
# session.add(f1)
# session.add(f2)

p = session.query(Paper).filter(Paper.id==1).first()
print(p)
print(p.title)

f = session.query(Fund).filter(Fund.agency_acronym=='INSF').first()
print(f.papers)
print(f.papers[1].title)
session.commit()
session.close()