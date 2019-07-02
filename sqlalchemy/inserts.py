import os
import json
import io
import time
# import winsound
import datetime

from base import Session, engine, Base
from functions import data_inspector
from temp import keyword_process, source_process, fund_process, \
    author_process, paper_process, \
    ext_country_process, ext_subject_process, \
    ext_source_process, ext_source_metric_process

from associations import Paper_Author

Base.metadata.create_all(engine)
session = Session()

start = time.time()

# frequency = 2000  # Set Frequency (Hz)
# duration = 300  # Set Duration (ms)

# ==============================================================================
# External Datasets
# ==============================================================================

# countries
print('@ countries')
session.bulk_save_objects(
    ext_country_process(session, os.path.join('data', 'countries.csv')))
end = time.time()
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')

# subjects
print('@ subjects')
session.bulk_save_objects(
    ext_subject_process(session, os.path.join('data', 'subjects.csv')))
end = time.time()
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')

max_rows = 50000
max_inserts = 1000
total_batches = max_rows // max_inserts

# sources: journals
print('@ journals')
for i in range(total_batches):
    sources_list = ext_source_process(
        session, os.path.join('data', 'sources.csv'), 
        src_type='Journal', 
        chunk_size=max_inserts, batch_no=(i + 1)
    )
    if source_process:
        for source in sources_list:
            session.add(source)
    session.commit()
end = time.time()
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')

# sources: conference proceedings
print('@ conference proceedings')
for i in range(total_batches):
    sources_list = ext_source_process(
        session, os.path.join('data', 'conferences.csv'),
        src_type='Conference Proceedings', 
        chunk_size=max_inserts, batch_no=(i + 1)
    )
    if source_process:
        for source in sources_list:
            session.add(source)
    session.commit()
end = time.time()
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')

# source metrics
print('@ source metrics')
for y in range(2018, 2010, -1):
    for i in range(total_batches):
        sources_list = ext_source_metric_process(
            session, os.path.join('data', f'scimagojr {y}.csv'), y,
            chunk_size=max_inserts, batch_no=(i + 1)
        )
        session.commit()
end = time.time()
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')

# ==============================================================================
# Papers
# ==============================================================================

print('@ papers')
bad_papers = []

path = os.path.join('data', 'Sharif University of Technology')
files = list(os.walk(path))[0][2]
files.sort()
flag = False
for file in files:
    if file.split('.')[1] != 'txt':
        continue
    if flag:
        break
    print(file)
    with io.open(os.path.join(path, file), 'r', encoding='utf8') as raw:
        data = json.load(raw)
        data = data['search-results']['entry']
        retrieval_time = datetime.datetime \
            .utcfromtimestamp(int(file.split('.')[0].split('_')[-1])) \
            .strftime('%Y-%m-%d %H:%M:%S')
        
        for cnt, entry in enumerate(data):
            warnings = data_inspector(entry)
            try:
                keys = entry.keys()
                if 'dc:identifier' in warnings:
                    bad_papers.append(
                        {'file': file, 'paper_no': cnt,
                         'problem': [warn for warn in warnings]}
                    )
                    continue
                if 'openaccess' in warnings:
                    bad_papers.append(
                        {'file': file, 'paper_no': cnt, 'id_scp': entry['dc:identifier'], 
                        'problem': [warn for warn in warnings]}
                    )
                    entry['openaccess'] = '0'
                    warnings.remove('openaccess')
                if 'author:afid' in warnings:
                    bad_papers.append(
                        {'file': file, 'paper_no': cnt, 'id_scp': entry['dc:identifier'], 
                        'problem': [warn for warn in warnings]}
                    )
                    warnings.remove('author:afid')
                if 'dc:title' in warnings:
                    bad_papers.append(
                        {'file': file, 'paper_no': cnt, 'id_scp': entry['dc:identifier'], 
                        'problem': [warn for warn in warnings]}
                    )
                    entry['dc:title'] = 'TITLE NOT AVAILABLE'
                    warnings.remove('dc:title')
                if warnings:
                    bad_papers.append(
                        {'file': file, 'paper_no': cnt, 'id_scp': entry['dc:identifier'], 
                        'problem': [warn for warn in warnings]}
                    )
                    continue
                
                paper = paper_process(session, entry, retrieval_time, keys)
                
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
                print(type(e))
                session.close()
                print('\a')
                # winsound.Beep(frequency, duration)
                bad_papers.append(
                    {'file': file, 'paper_no': cnt, 'id_scp': entry['dc:identifier'],
                     'problem': f'{type(e)}: {e}'}
                )
                print(file)
                print(entry['dc:identifier'])
                print()
                print('!!!')
                print('ERROR: ', e)
                print('--------------------------------------------------')
                flag = True
                break

session.commit()

# ==============================================================================
# Exporting logs
# ==============================================================================

with io.open(os.path.join('logs', 'bad_papers.json'), 
    'w', encoding='utf8') as log:
    json.dump(bad_papers, log, indent=4)

end = time.time()
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')
session.close()
