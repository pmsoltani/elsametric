import os
import json
import io
from time import time, strftime, gmtime
from datetime import datetime

from elsametric.models.base import engine, Session, Base
from elsametric.helpers.process import file_process
from elsametric.helpers.process import ext_country_process
from elsametric.helpers.process import ext_subject_process
from elsametric.helpers.process import ext_source_process
from elsametric.helpers.process import ext_source_metric_process
from elsametric.helpers.process import ext_faculty_process


# ==============================================================================
# Config
# ==============================================================================


config_path = os.path.join(os.getcwd(), 'config.json')
with io.open(config_path, 'r') as config_file:
    config = json.load(config_file)

config = config['database']['populate']

Base.metadata.create_all(engine)
session = Session()

data_path = config['data_directory']

t0 = time()  # timing the entire process


# ==============================================================================
# External Datasets
# ==============================================================================


# countries
if config['countries']['process']:
    print('@ countries')

    countries_list = ext_country_process(
        session, os.path.join(data_path, config['countries']['path']))
    if countries_list:
        session.add_all(countries_list)
    session.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# subjects
if config['subjects']['process']:
    print('@ subjects')

    subjects_list = ext_subject_process(
        session, os.path.join(data_path, config['subjects']['path']))
    if subjects_list:
        session.add_all(subjects_list)
    session.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# sources: journals
if config['journals']['process']:
    print('@ journals')

    sources_list = ext_source_process(
        session, os.path.join(data_path, config['journals']['path']),
        src_type='Journal')
    if sources_list:
        session.add_all(sources_list)
    session.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# sources: conference proceedings
if config['conferences']['process']:
    print('@ conference proceedings')

    sources_list = ext_source_process(
        session, os.path.join(data_path, config['conferences']['path']),
        src_type='Conference Proceeding')
    if sources_list:
        session.add_all(sources_list)
    session.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# source metrics
for item in config['metrics']:
    if not item['process']:
        continue
    print(f'@ metrics: {item["path"]}')

    sources_list = ext_source_metric_process(
        session, os.path.join(data_path, item['path']), item['year'])
    session.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# ==============================================================================
# Papers
# ==============================================================================


for item in config['papers']:
    if not item['process']:
        continue
    print(f'@ papers for: {item["path"]}')

    institution_bad_papers = []
    path = os.path.join(data_path, item['path'])
    files = list(os.walk(path))[0][2]
    files.sort()

    for file in files:
        # skipping files like 'thumbs.db'
        if file.split('.')[1] not in ['json', 'txt']:
            continue

        print(file)
        file_path = os.path.join(path, file)
        retrieval_time = datetime \
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
            institution_bad_papers.append(problems)

        session.commit()

    if institution_bad_papers:
        log_folder = os.path.join(data_path, config['logs'])
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        log_name = f'bad_papers_{item["path"]}_{int(time())}.json'
        with io.open(os.path.join(log_folder, log_name),
                    'w', encoding='utf8') as log:
            json.dump(institution_bad_papers, log, indent=4)

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')

session.close()


# ==============================================================================
# Institutions' faculty & department data
# ==============================================================================


for item in config['institutions']:
    if not item['process']:
        continue
    print(f'@ faculties & departments for: {item["id_scp"]}: {item["name"]}')

    faculties_list = ext_faculty_process(
        session,
        os.path.join(data_path, item['faculties']),
        os.path.join(data_path, item['departments']),
        institution_id_scp=item['id_scp']
    )
    session.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')

session.close()
