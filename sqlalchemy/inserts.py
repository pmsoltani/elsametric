from base import Session, engine, Base
from functions import *

from country import Country
from subject import Subject
from source import Source
from fund import Fund
from paper import Paper
from keyword_ import Keyword
from author import Author
from author_profile import Author_Profile
from institution import Institution
from institution_alias import Institution_Alias
from department import Department
from department_alias import Department_Alias
from associations import Paper_Author

Base.metadata.create_all(engine)
session = Session()

import json
import os
import io
import csv
import time
import winsound
from sys import getsizeof
from collections import OrderedDict
import datetime

start = time.time()
max_inserts = 1000

frequency = 2000  # Set Frequency (Hz)
duration = 300  # Set Duration (ms)
# winsound.Beep(frequency=frequency, duration=duration)

# countries = []
# with io.open('countries.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for row in reader:
#         country = Country(
#             name=row['name'], domain=row['domain'],
#             region=row['region'], sub_region=row['sub_region']
#         )
#         query = session.query(Country) \
#             .filter(Country.name == country.name) \
#             .first()
#         if query:
#             continue
#         session.add(country)
#         countries.append(country)

# session.commit()

# subjects = []
# with io.open('subjects.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for row in reader:
#         subject = Subject(
#             asjc=row['asjc'],
#             top=row['top'], middle=row['middle'], low=row['low']
#         )
#         query = session.query(Subject) \
#             .filter(Subject.asjc == subject.asjc) \
#             .first()
#         if query:
#             continue
#         session.add(subject)
#         subjects.append(subject)

# session.commit()

# with io.open('sources.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for cnt, row in enumerate(reader):
#         for item in row:
#             if not row[item]:
#                 row[item] = None
#         source = Source(
#             id_scp=row['id_scp'], title=row['title'], type=row['type'],
#             issn=row['issn'], e_issn=row['e_issn'], publisher=row['publisher']
#         )
#         query = session.query(Source) \
#             .filter(Source.id_scp == source.id_scp) \
#             .first()
#         if query:
#             continue
#         country = country_name(row['country'])
#         if country:
#             query = session.query(Country) \
#                 .filter(Country.name == country) \
#                 .first()
#             source.country = query
#         if row['asjc']:
#             subject_codes = [int(code) 
#                            for code in row['asjc'].split(';') if code != '']
#             for code in subject_codes:
#                 query = session.query(Subject) \
#                     .filter(Subject.asjc == code) \
#                     .first()
#                 if query:
#                     source.subjects.append(query)

#         session.add(source)
#         # sources.append(source)
#         if (cnt + 1) % max_inserts == 0:
#             session.commit()
#             # sources = []
        
# try:
#     session.commit()
# except:
#     print('nothing to commit')
# finally:
#     session.close()


file = 'Sharif University of Technology_y2011_001_OSNURM_1558340225.txt'
with io.open(file, 'r', encoding='utf8') as raw:
    data = json.load(raw)
    data = data['search-results']['entry']
    ret_time = datetime.datetime \
        .utcfromtimestamp(int(file.split('.')[0].split('_')[-1])) \
        .strftime('%Y-%m-%d %H:%M:%S')
    
    for entry in data:
        warnings = data_inspector(entry)
        print(file)
        print(entry['dc:identifier'])
        try:
            result = {'msg': '', 'value': None}
            if 'openaccess' in warnings:
                entry['openaccess'] = '0'
                warnings.remove('openaccess')
            if 'author:afid' in warnings:
                warnings.remove('author:afid')
            if warnings:
                result['msg'] = warnings
                print('!!!')
                print(result)
                continue

            keys = entry.keys()

            paper_url = ''
            for link in entry['link']:
                if link['@ref'] == 'scopus':
                    print('Paper URL found!')
                    paper_url = link['@href']
                    break

            paper_id_scp = int(entry['dc:identifier'].split(':')[1])
            paper = session.query(Paper) \
                .filter(Paper.id_scp == paper_id_scp) \
                .first()
            if paper:
                result['msg'] = 'paper exists'
                result['value'] = paper.id
                print(result)
                print('---------------------')
                continue
            
            source_id_scp = int(entry['source-id'])
            source = session.query(Source) \
                .filter(Source.id_scp == source_id_scp) \
                .first()
            if not source:
                print(f'Source with id_scp: {source_id_scp} not found. Adding it.')
                source = Source(
                    id_scp=source_id_scp,
                    title=key_get(entry, keys, 'prism:publicationName'),
                    type=key_get(entry, keys, 'prism:aggregationType'),
                    issn=strip(key_get(entry, keys, 'prism:issn'), max_length=8),
                    e_issn=strip(key_get(entry, keys, 'prism:eIssn'), max_length=8),
                    isbn=strip(key_get(entry, keys, 'prism:isbn'), max_length=13),
                )
                session.add(source)
            
            fund = None
            fund_id_scp = key_get(entry, keys, 'fund-no')
            if fund_id_scp == 'undefined':
                fund_id_scp = None
            agency = key_get(entry, keys, 'fund-sponsor')
            agency_acronym = key_get(entry, keys, 'fund-acr')
            if fund_id_scp and agency:
                fund = session.query(Fund) \
                    .filter(Fund.id_scp == fund_id_scp, Fund.agency == agency) \
                    .first()
            elif fund_id_scp:
                fund = session.query(Fund) \
                    .filter(Fund.id_scp == fund_id_scp) \
                    .first()
            elif agency:
                fund = session.query(Fund) \
                    .filter(Fund.agency == agency) \
                    .first()
            
            if any(item for item in [fund_id_scp, agency]) and (not fund):
                print('Info about fund exists, but cannot be found on the db. Adding it.')
                fund = Fund(
                    id_scp=fund_id_scp,
                    agency=agency, agency_acronym=agency_acronym
                )
            
            paper = Paper(
                id_scp=paper_id_scp,
                eid=key_get(entry, keys, 'eid'),
                title=key_get(entry, keys, 'dc:title'),
                type=key_get(entry, keys, 'subtype'),
                type_description=key_get(entry, keys, 'subtypeDescription'),
                abstract=key_get(entry, keys, 'dc:description'),
                total_author=key_get(entry, keys, 'author-count'),
                open_access=int(key_get(entry, keys, 'openaccess')),
                cited_cnt=key_get(entry, keys, 'citedby-count'),
                url=paper_url,
                article_no=key_get(entry, keys, 'article-number'),
                doi=key_get(entry, keys, 'prism:doi'),
                volume=key_get(entry, keys, 'prism:volume'),
                issue=key_get(entry, keys, 'prism:issueIdentifier'),
                date=key_get(entry, keys, 'prism:coverDate'),
                page_range=key_get(entry, keys, 'prism:pageRange'),
                retrieval_time=ret_time,
            )
            paper.source = source
            paper.fund = fund
            print(f'Paper object for id_scp: {paper_id_scp} created.')

            for auth in entry['author']:
                keys = auth.keys()
                author_id_scp = int(auth['authid'])
                paper_author = Paper_Author(int(auth['@seq']))
                author = session.query(Author) \
                    .filter(Author.id_scp == author_id_scp) \
                    .first()
                if not author:
                    print(f'Author with id_scp: {author_id_scp} not found. Adding it.')
                    author = Author(
                        id_scp=author_id_scp,
                        first=key_get(auth, keys, 'given-name'),
                        last=key_get(auth, keys, 'surname'),
                        initials=key_get(auth, keys, 'initials')
                    )

                    author_profile = Author_Profile(
                        address=f'https://www.scopus.com/authid/detail.uri?authorId={author_id_scp}',
                        type='Scopus Profile',
                    )
                    author.profiles.append(author_profile)
                else:
                    print(f'Author with id_scp: {author_id_scp} found by id: {author.id}')
                paper_author.author = author
                paper.authors.append(paper_author)
                print('Link between Paper and Author objects created')
                session.add(paper)
                session.commit()
            print('---------------------')
        except Exception as e:
            winsound.Beep(frequency, duration)
            print(e)
            break

session.commit()









end = time.time()

# print(f'countries: {getsizeof(countries)}, len: {len(countries)}')
# print(f'subjects: {getsizeof(subjects)}, len: {len(subjects)}')
# # print(f'sources: {getsizeof(sources)}, len: {len(sources)}')
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')

# sources = session.query(Source) \
#     .all()

# print()
# print(len(sources))
# print(sources[0])
# print(0, sources[0].title)
# print(100, sources[100].title)
# session.close()