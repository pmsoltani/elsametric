import io
import csv
import json

import requests as req
from bs4 import BeautifulSoup
from furl import furl
from pathlib import Path

from helpers import get_row, exporter, nullify, upper_first, new_columns


# ==============================================================================
# Config
# ==============================================================================


CURRENT_DIR = Path.cwd()
with io.open(CURRENT_DIR / 'crawlers_config.json', 'r') as config_file:
    config = json.load(config_file)
config = config['institutions']['Tarbiat Modares University']

DATA_PATH = CURRENT_DIR / config['data_directory']
FACULTY_LIST_PATH = DATA_PATH / config['faculties_list_raw']
FACULTY_DETAILS_PATH = DATA_PATH / config['faculties_details_raw']
ERRORS_LOG_PATH = DATA_PATH / config['errors_log']
BASE = config['base_url']
FACULTIES_LIST_URL = config['faculties_list_url']
FIRST_FACULTY_ID = config['first_faculty_id']

HEADERS = {'User-Agent': config['user_agent']}
FA_ALPHABET = 'اآبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'
EN_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


# ==============================================================================
# Step 1: Get a list of faculties for each alphabet letter and export them
# ==============================================================================


first_time = True
for let in FA_ALPHABET:
    print(f'Page {let}/{FA_ALPHABET[-1]} ...', end=' ')

    try:
        page = req.get(url=FACULTIES_LIST_URL, headers=HEADERS,
                       params={'serviceid': 792, 'k': let})  # hard-coded value
        page.raise_for_status()
        raw_faculties = BeautifulSoup(page.text, 'html.parser').find_all('tr')
    except (AttributeError, req.HTTPError):
        print('error (page not available)')
        continue

    parsed_faculties = []
    for faculty in raw_faculties:
        f = furl(BASE)
        faculty_email = next(
            filter(lambda td: '@' in td.text, faculty.find_all('td')))
        faculty_email = faculty_email.text.strip()
        faculty_id = faculty_email.split('@')[0].strip()
        faculty_url = faculty.find('a')
        f.path = faculty_url['href'].strip()
        faculty_name = [name.strip() for name in faculty_url.text.split('،')]
        parsed_faculties.append({
            'First Fa': faculty_name[1],
            'Last Fa': faculty_name[0],
            'First En': None,
            'Last En': None,
            'Department En': None,
            'Institution ID': faculty_id,
            'Personal Website': f.url,
            'Email': faculty_email
        })

    exporter(FACULTY_LIST_PATH, parsed_faculties,
             reset=first_time, bulk=True, headers=first_time)
    first_time = False
    print('exported')


# ==============================================================================
# Step 2: Use English faculty list to get English first & last names separately
# ==============================================================================


# load the previously exported faculty_list all at once:
faculties = []
cnt = 0
with io.open(FACULTY_LIST_PATH, 'r', encoding='utf-8') as csv_file:
    reader = csv.DictReader(csv_file, delimiter=',')
    for row in reader:
        faculties.append(row)

print('\n\nProcessing English first & last names ...')
for let in EN_ALPHABET:
    print(f'Page {let}/{EN_ALPHABET[-1]} ...', end=' ')
    try:
        page = req.get(url=FACULTIES_LIST_URL, headers=HEADERS,
                       params={'serviceid': 1033, 'k': let})  # hard-coded value
        page.raise_for_status()
        raw_faculties = BeautifulSoup(page.text, 'html.parser').find_all('tr')
    except (AttributeError, req.HTTPError):
        print('error (page not available)')
        continue

    for faculty in raw_faculties:
        faculty_url = faculty.find('a')
        faculty_id = furl(faculty_url['href']) \
            .path.segments[-1].strip().replace('~', '')
        cnt += 1
        faculty_name = [name.strip() for name in faculty_url.text.split(',')]
        faculty_department = faculty.find_all('td')[2].text.strip()
        index = next(
            (i for (i, row) in enumerate(faculties)
             if row['Institution ID'] == faculty_id),
            None
        )
        if index is not None:
            faculties[index]['First En'] = upper_first(faculty_name[1])
            faculties[index]['Last En'] = upper_first(faculty_name[0])
            faculties[index]['Department En'] = faculty_department
    print('done')

exporter(FACULTY_LIST_PATH, faculties, reset=True, bulk=True, headers=True)
print('done')


# ==============================================================================
# Step 3: Crawl the 'Personal Website' of each faculty and export the results
# ==============================================================================


contact_icon_type_mapper = {
    'fa-envelope': None,  # Email address, which is already collected: skip it
    'fa-globe': 'Scopus ID',
    'fa-google': 'Google Scholar ID',
    'fa-phone': 'Office',
    'fa-fax': 'Fax',
    'fa-link': None,  # Personal Website, which is already collected: skip it
    'fa-line-chart': None  # research.ac.ir ID, which is not needed: skip it
}
rank_fa_en_mapper = {
    'استادیار': 'Assistant Professor',
    'دانشیار': 'Associate Professor',
    'استاد': 'Full Professor'
}
rows = get_row(FACULTY_LIST_PATH)
COLUMNS = ['Profile Picture URL', 'Faculty Fa', 'Department Fa', 'Rank Fa',
           'Rank', 'Office', 'Fax', 'Scopus ID', 'Google Scholar ID']
errors = []
csv_headers = not Path(FACULTY_DETAILS_PATH).is_file()
first_faculty_crawled = not FIRST_FACULTY_ID or False  # no config => crawl all
for row in rows:
    if not row['Institution ID']:
        continue

    print(f'ID: {row["Institution ID"]} ...', end=' ')
    f = furl(BASE)
    new_columns(row, COLUMNS, None)

    if row['Institution ID'] == FIRST_FACULTY_ID:  # reached the first faculty
        first_faculty_crawled = True
    if not first_faculty_crawled:  # first faculty (in config) not reached yet
        print('skipping (config)')
        continue
    if not row['Personal Website']:  # faculty page not available
        exporter(FACULTY_DETAILS_PATH, [row], headers=csv_headers)
        csv_headers = False
        print('error (page not available) ... exported')
        continue

    try:  # requesting faculty's page
        page_fa = req.get(url=row['Personal Website'],
                          allow_redirects=False, headers=HEADERS)
        page_fa.raise_for_status()
        soup = BeautifulSoup(page_fa.text, 'html.parser')
    except req.HTTPError as e:
        exporter(FACULTY_DETAILS_PATH, [row], headers=csv_headers)
        csv_headers = False
        errors.append({
            'type': str(type(e)), 'msg': str(e), 'section': 'page',
            'id': row['Institution ID']})
        print('error (page not available) ... exported')
        continue

    try:  # faculty's profile picture
        faculty_picture_path = soup \
            .find('img', attrs={'class': 'img-thumbnail'})['src']
        f.path = faculty_picture_path
        row['Profile Picture URL'] = f.url
        print('Profile picture done ...', end=' ')
    except KeyError as e:  # profile picture url not found
        print('Profile picture error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': None, 'section': 'profile picture',
            'id': row['Institution ID']})
        pass

    page_header = soup.find('div', attrs={'class': 'pageheader'})
    try:  # faculty's faculty (upper department) & academic rank
        faculty_faculty = page_header.find('h3').find('a')

        row['Faculty Fa'] = faculty_faculty.text.strip()
        row['Rank Fa'] = faculty_faculty.previous_sibling.strip()
        row['Rank'] = rank_fa_en_mapper[row['Rank Fa']]
        print('Faculty & Rank done ...', end=' ')
    except AttributeError as e:
        print('Faculty & Rank error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': None, 'section': 'faculty & rank',
            'id': row['Institution ID']})
        pass
    except KeyError as e:
        print(f'error (english counterpart for {row["Rank Fa"]} not found)')

    try:  # faculty's department
        row['Department Fa'] = page_header \
            .find('p', attrs={'class': 'uni-grp'}) \
            .find('a').text.strip()
        print('Department done ...', end=' ')
    except AttributeError as e:
        print('Department error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': None, 'section': 'department',
            'id': row['Institution ID']})
        pass

    try:  # faculty's contact info
        faculty_contacts = soup \
            .find('div', attrs={'class': 'pagecontents'}) \
            .find('div', attrs={'class': 'row'}) \
            .find_all('div', recursive=False)[1] \
            .find('ul', attrs={'class': 'list-unstyled'}) \
            .find_all('li')

        for contact in faculty_contacts:
            try:
                # format: ['fa', 'fa-icon'] -> select the 2nd class name
                contact_icon = contact.find('i')['class'][1]
                contact_type = contact_icon_type_mapper[contact_icon]
            except (KeyError, TypeError) as e:  # contact type not found
                contact_type = None

            if not contact_type:
                contact_type

            if contact_type in ['Google Scholar ID', 'Scopus ID']:
                contact_info = contact.find('span').find('a')['href']
                try:
                    row['Google Scholar ID'] = furl(contact_info).args['user']
                except KeyError:  # no valid google scholar id found, try scopus
                    try:
                        row['Scopus ID'] = furl(contact_info).args['authorId']
                    except KeyError:  # no valid scopus id found, either
                        pass

            if contact_type in ['Office', 'Fax']:
                contact_info = contact \
                    .find('span').text.strip().replace(' ', '')
                row[contact_type] = contact_info

        print('Contacts done ...', end=' ')
    except (AttributeError, TypeError) as e:
        print('Contacts error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': None, 'section': 'contact',
            'id': row['Institution ID']})
        pass

    nullify(row)
    exporter(FACULTY_DETAILS_PATH, [row], headers=csv_headers)
    csv_headers = False
    print('exported')

if errors:
    csv_headers = not Path(ERRORS_LOG_PATH).is_file()
    exporter(ERRORS_LOG_PATH, errors, bulk=True, headers=csv_headers)
    print()
    print('error logs exported')
