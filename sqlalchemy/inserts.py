import os
import json
import io
import time
import datetime

from base import Session, engine, Base

from temp import file_process
from temp import paper_process
from temp import keyword_process
from temp import source_process
from temp import fund_process
from temp import author_process
from temp import ext_country_process
from temp import ext_subject_process
from temp import ext_source_process
from temp import ext_source_metric_process
from temp import ext_faculty_process

Base.metadata.create_all(engine)
session = Session()

start = time.time()

# ==============================================================================
# External Datasets
# ==============================================================================

# countries
print('@ countries')
session.bulk_save_objects(
    ext_country_process(session, os.path.join('data', 'countries.csv')))
session.commit()
print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time()-start))}')

# subjects
print('@ subjects')
session.bulk_save_objects(
    ext_subject_process(session, os.path.join('data', 'subjects.csv')))
session.commit()
print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time()-start))}')

max_rows = 50000  # an estimate of available sources within a .csv file
max_inserts = 1000  # the size of chunks for big .csv files
total_batches = max_rows // max_inserts

# sources: journals
print('@ journals')
for i in range(total_batches):
    sources_list = ext_source_process(
        session, os.path.join('data', 'sources.csv'), 
        src_type='Journal', 
        chunk_size=max_inserts, batch_no=(i + 1))
    if sources_list:
        session.add_all(sources_list)
    session.commit()
print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time()-start))}')

# sources: conference proceedings
print('@ conference proceedings')
for i in range(total_batches):
    sources_list = ext_source_process(
        session, os.path.join('data', 'conferences.csv'),
        src_type='Conference Proceedings', 
        chunk_size=max_inserts, batch_no=(i + 1))
    if sources_list:
        session.add_all(sources_list)
    session.commit()
print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time()-start))}')

# source metrics
print('@ source metrics')
for y in range(2018, 2010, -1):
    for i in range(total_batches):
        sources_list = ext_source_metric_process(
            session, os.path.join('data', f'scimagojr {y}.csv'), y,
            chunk_size=max_inserts, batch_no=(i + 1)
        )
        session.commit()
print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time()-start))}')

# ==============================================================================
# Papers
# ==============================================================================

print('@ papers')
all_bad_papers = []
path = os.path.join('data', 'Sharif University of Technology')
files = list(os.walk(path))[0][2]
files.sort()

for file in files:
    # skipping files like 'thumbs.db'
    if file.split('.')[1] not in ['json', 'txt']:
        continue
    
    print(file)
    file_path = os.path.join(path, file)
    retrieval_time = datetime.datetime \
        .utcfromtimestamp(int(file.split('.')[0].split('_')[-1])) \
        .strftime('%Y-%m-%d %H:%M:%S')
    (problems, papers_list) = file_process(
        session, file_path, retrieval_time, encoding='utf8')
    if 'error_msg' in problems.keys():  # there was an exception: can't go on
        print()
        print(problems['file'])
        print(problems['id_scp'])
        print(problems['error_type'])
        print(problems['error_msg'])
        break
    
    if papers_list:
        session.add_all(papers_list)
    if problems:
        all_bad_papers.append(problems)
    
    session.commit()
session.close()

print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time()-start))}')

# ==============================================================================
# Faculties
# ==============================================================================

print('@ faculties')
inst_id = 60027666
faculties_list = ext_faculty_process(
    session, 
    os.path.join('data', 'Faculties.csv'), 
    os.path.join('data', 'Departments.csv'),
    institution_id_scp=inst_id
)

session.commit()
print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time()-start))}')

# ==============================================================================
# Exporting logs
# ==============================================================================

if all_bad_papers:
    log_file_path = f'bad_papers_{int(time.time())}.json'
    with io.open(os.path.join('logs', log_file_path),
                 'w', encoding='utf8') as log:
        json.dump(all_bad_papers, log, indent=4)

session.close()
