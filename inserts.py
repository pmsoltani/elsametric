import os
import json
import io
import time
import datetime

from elsametric.db_classes.base import engine, Session, Base

from elsametric.helpers.process import file_process
from elsametric.helpers.process import ext_country_process
from elsametric.helpers.process import ext_subject_process
from elsametric.helpers.process import ext_source_process
from elsametric.helpers.process import ext_source_metric_process
from elsametric.helpers.process import ext_faculty_process

Base.metadata.create_all(engine)
session = Session()

data_path = os.path.abspath(__file__)
for d in range(2):  # going up 2 directories
    data_path = os.path.dirname(data_path)
data_path = os.path.join(data_path, 'data')

t0 = time.time()  # timing the entire process

# ==============================================================================
# External Datasets
# ==============================================================================

# # countries
# print('@ countries')
# session.bulk_save_objects(
#     ext_country_process(session, os.path.join(data_path, 'countries.csv')))
# session.commit()
# print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')

# # subjects
# print('@ subjects')
# session.bulk_save_objects(
#     ext_subject_process(session, os.path.join(data_path, 'subjects.csv')))
# session.commit()
# print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')

# # sources: journals
# print('@ journals')
# sources_list = ext_source_process(
#     session, os.path.join(data_path, 'sources.csv'),
#     src_type='Journal')
# if sources_list:
#     session.add_all(sources_list)
# session.commit()
# print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')

# # sources: conference proceedings
# print('@ conference proceedings')
# sources_list = ext_source_process(
#     session, os.path.join(data_path, 'conferences.csv'),
#     src_type='Conference Proceeding')
# if sources_list:
#     session.add_all(sources_list)
# session.commit()
# print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')

# # metrics1
# print('@ metrics1')
# for y in range(2018, 2010, -1):
#     sources_list = ext_source_metric_process(
#         session, os.path.join(data_path, f'{y}.csv'), y)
# session.commit()
# print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')

# ==============================================================================
# Papers
# ==============================================================================

print('@ papers')
institution_names = [
    # 'Sharif University of Technology',
    # 'Amirkabir University of Technology',
    # 'Shahid Beheshti University',
    # 'Tarbiat Modares University',
    # 'University of Tehran',
    'Iran Polymer and Petrochemical Institute',
]

for institution_name in institution_names:
    all_bad_papers = []
    path = os.path.join(data_path, institution_name)
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
        if 'error_msg' in problems.keys():  # there was an exception: break
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

    if all_bad_papers:
        log_folder = os.path.join(data_path, 'logs')
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        log_name = f'bad_papers_{institution_name}_{int(time.time())}.json'
        with io.open(os.path.join(log_folder, log_name),
                     'w', encoding='utf8') as log:
            json.dump(all_bad_papers, log, indent=4)

session.close()

print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')

# ==============================================================================
# Faculties
# ==============================================================================

# print('@ faculties')
# inst_id = 60027666
# faculties_list = ext_faculty_process(
#     session,
#     os.path.join(data_path, 'Faculties.csv'),
#     os.path.join(data_path, 'Departments.csv'),
#     institution_id_scp=inst_id
# )
# session.commit()
# print(f'Op. Time: {time.strftime("%H:%M:%S", time.gmtime(time.time() - t0))}')

# session.close()
