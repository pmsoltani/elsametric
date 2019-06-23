import os
import json
import io
import time
import winsound
import datetime

from base import Session, engine, Base
from functions import data_inspector
from temp import keyword_process, source_process, fund_process, \
    author_process, paper_process, \
    ext_country_process, ext_subject_process, ext_source_process

from associations import Paper_Author

Base.metadata.create_all(engine)
session = Session()

start = time.time()
max_inserts = 1000

frequency = 2000  # Set Frequency (Hz)
duration = 300  # Set Duration (ms)

# ==============================================================================
# External Datasets
# ==============================================================================

# # countries
# session.bulk_save_objects(ext_country_process(session, 'countries.csv'))

# # subjects
# session.bulk_save_objects(ext_subject_process(session, 'subjects.csv'))

# # sources: journals
# for i in range(50):
#     sources_list = ext_source_process(
#         session, 'sources.csv', 
#         src_type='Journal', 
#         chunk_size=1000, batch_no=(i + 1)
#     )
#     if source_process:
#         for source in sources_list:
#             session.add(source)
#     session.commit()

# # sources: conference proceedings
# for i in range(50):
#     sources_list = ext_source_process(
#         session, 'conferences.csv', 
#         src_type='Conference Proceedings', 
#         chunk_size=1000, batch_no=(i + 1)
#     )
#     if source_process:
#         for source in sources_list:
#             session.add(source)
#     session.commit()

# ==============================================================================
# Papers
# ==============================================================================

path = 'C:\\Users\\pmsoltani\\Downloads\\Git\\elsametric\\data\\Sharif University of Technology'
files = list(os.walk(path))[0][2]
# file = 'Sharif University of Technology_y2018_005_S9J79E_1558880320.txt'
flag = False
for file in files:
    if flag:
        break
    with io.open(os.path.join(path, file), 'r', encoding='utf8') as raw:
        data = json.load(raw)
        data = data['search-results']['entry']
        ret_time = datetime.datetime \
            .utcfromtimestamp(int(file.split('.')[0].split('_')[-1])) \
            .strftime('%Y-%m-%d %H:%M:%S')
        
        for entry in data:
            warnings = data_inspector(entry)
            try:
                if 'openaccess' in warnings:
                    entry['openaccess'] = '0'
                    warnings.remove('openaccess')
                if 'author:afid' in warnings:
                    warnings.remove('author:afid')
                if warnings:
                    print(file)
                    print(entry['dc:identifier'])
                    print()
                    print('!!!')
                    print('ERROR: ', warnings)
                    print('--------------------------------------------------')
                    continue
                
                keys = entry.keys()
                paper = paper_process(session, entry, ret_time, keys)
                
                if not paper.source:
                    paper.source = source_process(session, entry, keys)
                # if not paper.fund:
                #     paper.fund = fund_process(session, entry, keys)
                if not paper.keywords:
                    paper.keywords = keyword_process(session, entry, keys)
                if not paper.authors:
                    authors_list = author_process(session, entry, log=False)
                    for auth in authors_list:
                        paper_author = Paper_Author(author_no=auth[0])
                        paper_author.author = auth[1]
                        paper.authors.append(paper_author)

                session.add(paper)
                session.commit()
            except Exception as e:
                session.close()
                winsound.Beep(frequency, duration)
                print(file)
                print(entry['dc:identifier'])
                print()
                print('!!!')
                print('ERROR: ', e)
                print('--------------------------------------------------')
                flag = True
                break

session.commit()

end = time.time()

print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')
session.close()