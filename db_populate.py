import json
import io
from pathlib import Path
from time import time, strftime, gmtime
from datetime import datetime

from elsametric.models.base import engine, SessionLocal, Base
from elsametric.helpers.process import file_process
from elsametric.helpers.process import ext_country_process
from elsametric.helpers.process import ext_subject_process
from elsametric.helpers.process import ext_source_process
from elsametric.helpers.process import ext_source_metric_process
from elsametric.helpers.process import ext_faculty_process


# ==============================================================================
# Config
# ==============================================================================


CURRENT_DIR = Path.cwd()
with io.open(CURRENT_DIR / 'config.json', 'r') as config_file:
    config = json.load(config_file)

config = config['database']['populate']

Base.metadata.create_all(engine)
db = SessionLocal()

DATA_PATH = CURRENT_DIR / config['data_directory']

t0 = time()  # timing the entire process


# ==============================================================================
# External Datasets
# ==============================================================================


# countries
if config['countries']['process']:
    print('@ countries')

    countries_list = ext_country_process(
        db, DATA_PATH / config['countries']['path'])
    if countries_list:
        db.add_all(countries_list)
    db.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# subjects
if config['subjects']['process']:
    print('@ subjects')

    subjects_list = ext_subject_process(
        db, DATA_PATH / config['subjects']['path'])
    if subjects_list:
        db.add_all(subjects_list)
    db.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# sources: journals
if config['journals']['process']:
    print('@ journals')

    sources_list = ext_source_process(
        db, DATA_PATH / config['journals']['path'],
        src_type='Journal')
    if sources_list:
        db.add_all(sources_list)
    db.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# sources: conference proceedings
if config['conferences']['process']:
    print('@ conference proceedings')

    sources_list = ext_source_process(
        db, DATA_PATH / config['conferences']['path'],
        src_type='Conference Proceeding')
    if sources_list:
        db.add_all(sources_list)
    db.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# source metrics
for item in config['metrics']:
    if not item['process']:
        continue
    print(f'@ metrics: {item["path"]}')

    sources_list = ext_source_metric_process(
        db, DATA_PATH / item['path'], item['year'])
    db.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')


# ==============================================================================
# Papers
# ==============================================================================


for item in config['papers']:
    if not item['process']:
        continue
    print(f'@ papers for: {item["path"]}')

    institution_bad_papers = []
    papers_path = DATA_PATH / item['path']
    files = list(papers_path.iterdir())
    files.sort()

    for file in files:
        # skipping files like 'thumbs.db'
        if file.suffix not in ['.json', '.txt']:
            continue

        print(file.name)
        retrieval_time = datetime \
            .utcfromtimestamp(int(file.stem.split('_')[-1])) \
            .strftime('%Y-%m-%d %H:%M:%S')
        (problems, papers_list) = file_process(
            db, file, retrieval_time, encoding='utf8')
        if 'error_msg' in problems:  # there was an exception: break
            print()
            print(problems['file'])
            print(problems['id_scp'])
            print(problems['error_type'])
            print(problems['error_msg'])
            break

        if papers_list:
            db.add_all(papers_list)
        if problems:
            institution_bad_papers.append(problems)

        db.commit()

    if institution_bad_papers:
        log_folder = DATA_PATH / config['logs']
        if not Path(log_folder).is_dir():
            log_folder.mkdir(parents=True, exist_ok=True)
        log_name = f'bad_papers_{item["path"]}_{int(time())}.json'
        with io.open(log_folder / log_name, 'w', encoding='utf8') as log:
            json.dump(institution_bad_papers, log, indent=4)

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')

db.close()


# ==============================================================================
# Institutions' faculty & department data
# ==============================================================================


for item in config['institutions']:
    if not item['process']:
        continue
    print(f'@ faculties & departments for: {item["id_scp"]}: {item["name"]}')

    faculties_list = ext_faculty_process(
        db,
        DATA_PATH / item['faculties'],
        DATA_PATH / item['departments'],
        institution_id_scp=item['id_scp']
    )
    db.commit()

    print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')

db.close()
