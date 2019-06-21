from base import Session, engine, Base
from functions import data_inspector, key_get, strip
from temp import keyword_process, source_process, fund_process, institution_process, author_process

from country import Country
from subject import Subject
from source import Source
from fund import Fund
from paper import Paper
from keyword_ import Keyword
from author import Author
from author_profile import Author_Profile
from institution import Institution
# from institution_alias import Institution_Alias
from department import Department
# from department_alias import Department_Alias
# from associations import Paper_Author

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

# insert external here

file = 'Sharif University of Technology_y2018_005_S9J79E_1558880320.txt'
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
        print()
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
                print('---------------------')
                continue

            keys = entry.keys()

            paper_url = ''
            for link in entry['link']:
                if link['@ref'] == 'scopus':
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
            paper.source = source_process(session, entry, keys)
            paper.fund = fund_process(session, entry, keys)

            author_keywords = key_get(data=entry, keys=keys, key='authkeywords')
            paper.keywords = keyword_process(session=session, author_keywords=author_keywords)
            
            authors_list = author_process(session, entry)
            if authors_list:
                for auth in authors_list:
                    session.add(auth)
            
            # session.add(paper)
            session.commit()
            print('---------------------')
        except Exception as e:
            session.close()
            winsound.Beep(frequency, duration)
            print(e)
            break

session.commit()

end = time.time()

# print(f'countries: {getsizeof(countries)}, len: {len(countries)}')
# print(f'subjects: {getsizeof(subjects)}, len: {len(subjects)}')
# # print(f'sources: {getsizeof(sources)}, len: {len(sources)}')
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')
session.close()