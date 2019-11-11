import json
import io
from pathlib import Path
from time import gmtime, strftime, time
from datetime import datetime

from sqlalchemy.orm import Session

from elsametric.models.base import Base, engine, SessionLocal
from elsametric.helpers.process import (
    ext_country_process,
    ext_subject_process,
    ext_source_process,
    ext_source_metric_process,
    ext_faculty_process,
    file_process,
)


# ==============================================================================
# Config
# ==============================================================================


CURRENT_DIR = Path.cwd()
with io.open(CURRENT_DIR / 'config.json', 'r') as config_file:
    config = json.load(config_file)

config = config['database']['populate']

Base.metadata.create_all(engine)
db: Session

DATA_PATH = CURRENT_DIR / config['data_directory']

t0 = time()  # timing the entire process


# ==============================================================================
# External Datasets
# ==============================================================================


# countries
try:
    db = SessionLocal()
    if config['countries']['process']:
        print('@ countries')

        countries_list = ext_country_process(
            db, DATA_PATH / config['countries']['path'])
        if countries_list:
            db.add_all(countries_list)
        db.commit()

        print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')
finally:
    db.close()


# subjects
try:
    db = SessionLocal()
    if config['subjects']['process']:
        print('@ subjects')

        subjects_list = ext_subject_process(
            db, DATA_PATH / config['subjects']['path'])
        if subjects_list:
            db.add_all(subjects_list)
        db.commit()

        print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')
finally:
    db.close()


# sources: journals
try:
    if config['journals']['process']:
        print('@ journals')

        db = SessionLocal()
        sources = ext_source_process(
            db, DATA_PATH / config['journals']['path'], src_type='Journal')
        for source in sources:
            db.add(source)
            db.commit()
            db.close()

        print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')
finally:
    db.close()


# sources: conference proceedings
try:
    if config['conferences']['process']:
        print('@ conference proceedings')

        db = SessionLocal()
        sources = ext_source_process(
            db, DATA_PATH / config['conferences']['path'],
            src_type='Conference Proceeding')
        for source in sources:
            db.add(source)
            db.commit()
            db.close()

        print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')
finally:
    db.close()


# source metrics
for item in config['metrics']:
    if not item['process']:
        continue
    try:
        print(f'@ metrics using gen: {item["path"]}')

        db = SessionLocal()
        sources = ext_source_metric_process(
            db, DATA_PATH / item['path'], item['year'])
        for source in sources:
            db.add(source)
            db.commit()
            db.close()

        print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')
    finally:
        db.close()


# ==============================================================================
# Papers
# ==============================================================================


for item in config['papers']:
    if not item['process']:
        continue
    try:
        db = SessionLocal()
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
                try:
                    json.dump(institution_bad_papers, log, indent=4)
                except Exception as e:
                    print(type(e), e)
                    print(institution_bad_papers)

        print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')
    finally:
        db.close()


# ==============================================================================
# Institutions' faculty & department data
# ==============================================================================


for item in config['institutions']:
    if not item['process']:
        continue
    try:
        db = SessionLocal()
        print(f'@ faculties of {item["id_scp"]}: {item["name"]}')

        faculties_list = ext_faculty_process(
            db,
            DATA_PATH / item['faculties'],
            DATA_PATH / item['departments'],
            institution_id_scp=item['id_scp']
        )
        db.commit()

        print(f'Op. Time: {strftime("%H:%M:%S", gmtime(time() - t0))}')
    finally:
        db.close()

db.close()
