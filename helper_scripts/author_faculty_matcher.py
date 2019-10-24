import io
import csv
import json
from pathlib import Path

from fuzzywuzzy import fuzz
from sqlalchemy import extract

from elsametric.models.base import SessionLocal
from elsametric.models.associations import Author_Department
from elsametric.models.associations import Paper_Keyword
from elsametric.models.associations import Paper_Author
from elsametric.models.associations import Source_Subject
from elsametric.models.author import Author
from elsametric.models.author_profile import Author_Profile
from elsametric.models.country import Country
from elsametric.models.department import Department
from elsametric.models.fund import Fund
from elsametric.models.institution import Institution
from elsametric.models.keyword_ import Keyword
from elsametric.models.paper import Paper
from elsametric.models.source import Source
from elsametric.models.source_metric import Source_Metric
from elsametric.models.subject import Subject

from helpers import get_row, new_columns, author_faculty_matcher, exporter


# ==============================================================================
# Config
# ==============================================================================


CURRENT_DIR = Path.cwd()
with io.open(CURRENT_DIR / 'config.json', 'r') as config_file:
    config = json.load(config_file)
config = config['database']['populate']

DATA_PATH = CURRENT_DIR / config['data_directory']


# ==============================================================================
# Script
# ==============================================================================


for item in config['institutions']:
    institution = item['name']
    print(f'{institution}:', end=' ')

    if not item['process']:
        print('skipping (config)')
        continue

    institution_id_scp = item['id_scp']
    cutoff = item['fuzzy_match_cutoff']
    faculties = get_row(DATA_PATH / item['faculties'])
    export_path = DATA_PATH / f'{institution}_scp.csv'

    db = SessionLocal()
    authors = db \
        .query(Author) \
        .join((Department, Author.departments)) \
        .join((Institution, Department.institution)) \
        .filter(Institution.id_scp == institution_id_scp) \
        .all()  # empty list if not found

    if not authors:
        print('skipping (no authors found)')
        continue

    csv_headers = not Path(export_path).is_file()
    print(f'processing ({len(authors)} authors found)')
    for faculty in faculties:
        print(f'{faculty["Institution ID"]} ...', end=' ')
        new_columns(faculty, ['Scopus ID', 'Scopus ID Confidence'], None)

        if faculty['Scopus ID']:  # faculty's Scopus ID already known
            print('skipping (Scopus ID already present)')
            exporter(export_path, [faculty],  headers=csv_headers)
            csv_headers = False
            continue

        try:
            initials = faculty['Initials En']
            if not initials:
                raise ValueError
        except (KeyError, ValueError):
            initials = faculty['First En'][0]

        matches, confidence_level = author_faculty_matcher(
            authors, faculty['First En'], faculty['Last En'], initials, cutoff)

        if matches:
            faculty['Scopus ID'] = ', '.join(str(match) for match in matches)
            faculty['Scopus ID Confidence'] = confidence_level
            print(f'found: {confidence_level} confidence')
        else:
            print('not found')

        exporter(export_path, [faculty],  headers=csv_headers)
        csv_headers = False
