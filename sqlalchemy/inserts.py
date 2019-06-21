from base import Session, engine, Base
from functions import data_inspector, key_get, strip
from temp import keyword_process, source_process, fund_process, author_process, paper_process

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
with io.open('conferences.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for cnt, row in enumerate(reader):
        for item in row:
            if not row[item]:
                row[item] = None
        source = Source(
            id_scp=row['id_scp'], title=row['title'], type='Conference Proceedings',
            issn=row['issn'],
        )
        query = session.query(Source) \
            .filter(Source.id_scp == source.id_scp) \
            .first()
        if query:
            continue
        if row['asjc']:
            subject_codes = [int(code) 
                             for code in row['asjc'].split(';') if code != '']
            for code in subject_codes:
                query = session.query(Subject) \
                    .filter(Subject.asjc == code) \
                    .first()
                if query:
                    source.subjects.append(query)

        session.add(source)
        # sources.append(source)
        if (cnt + 1) % max_inserts == 0:
            session.commit()
            # sources = []
        
try:
    session.commit()
except:
    print('nothing to commit')
finally:
    session.close()


# file = 'Sharif University of Technology_y2018_005_S9J79E_1558880320.txt'
# with io.open(file, 'r', encoding='utf8') as raw:
#     data = json.load(raw)
#     data = data['search-results']['entry']
#     ret_time = datetime.datetime \
#         .utcfromtimestamp(int(file.split('.')[0].split('_')[-1])) \
#         .strftime('%Y-%m-%d %H:%M:%S')
    
#     for entry in data:
#         warnings = data_inspector(entry)
#         print(file)
#         print(entry['dc:identifier'])
#         print()
#         try:
#             result = {'msg': '', 'value': None}
#             if 'openaccess' in warnings:
#                 entry['openaccess'] = '0'
#                 warnings.remove('openaccess')
#             if 'author:afid' in warnings:
#                 warnings.remove('author:afid')
#             if warnings:
#                 result['msg'] = warnings
#                 print('!!!')
#                 print(result)
#                 print('---------------------')
#                 continue
            
#             keys = entry.keys()
#             paper = paper_process(session, entry, keys)
            
#             if not paper.source:
#                 paper.source = source_process(session, entry, keys)
#             if not paper.fund:
#                 paper.fund = fund_process(session, entry, keys)
#             if not paper.keywords:
#                 author_keywords = key_get(entry, keys, 'authkeywords')
#                 paper.keywords = keyword_process(session, author_keywords)
            
#             # authors_list = author_process(session, entry)
#             # if authors_list:
#             #     for auth in authors_list:
#             #         session.add(auth)
            
#             # session.add(paper)
#             session.commit()
#             print('---------------------')
#         except Exception as e:
#             session.close()
#             winsound.Beep(frequency, duration)
#             print(e)
#             break

session.commit()

end = time.time()

# print(f'countries: {getsizeof(countries)}, len: {len(countries)}')
# print(f'subjects: {getsizeof(subjects)}, len: {len(subjects)}')
# # print(f'sources: {getsizeof(sources)}, len: {len(sources)}')
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')
session.close()