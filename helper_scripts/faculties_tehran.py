import io
import csv
import json

import requests as req
from bs4 import BeautifulSoup
from furl import furl
from pathlib import Path

from helpers import get_row, exporter, nullify


# ==============================================================================
# Config
# ==============================================================================


CURRENT_DIR = Path.cwd()
with io.open(CURRENT_DIR / 'config.json', 'r') as config_file:
    config = json.load(config_file)
config = config['crawlers']['University of Tehran']

DATA_PATH = CURRENT_DIR / config['data_directory']
FACULTY_LIST_PATH = DATA_PATH / config['faculties_list']
FACULTY_DETAILS_PATH = DATA_PATH / config['faculties_details']
ERRORS_LOG_PATH = DATA_PATH / config['errors_log']
BASE = config['base_url']
FIRST_PAGE = config['first_page']
FIRST_FACULTY_ID = config["first_faculty_id"]

AGT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'
HEADERS = {'User-Agent': AGT}

try:  # find the total number of pages
    page = req.get(url=BASE, headers=HEADERS)
    page.raise_for_status()
    last_page_url = BeautifulSoup(page.text, 'html.parser') \
        .find('ul', attrs={'class': 'pagination'}) \
        .find('li', attrs={'class': 'last'}) \
        .find('a')['href']  # format: https://ut.ac.ir/fa/faculty?page=1
    LAST_PAGE = int(furl(last_page_url).args['page'])
except (AttributeError, req.HTTPError):
    LAST_PAGE = 106  # hardcoded value


# ==============================================================================
# Step 1: Get a list of all faculties
# ==============================================================================


table_attrs = {'class': 'table table-striped table-bordered responsive-table'}
info_mapper = {
    'نام': 'First Fa',
    'نام خانوادگی': 'Last Fa',
    'دانشکده/گروه': 'Faculty & Department Fa',
    'رتبه': 'Rank Fa',
    'پست الکترونیکی': ''  # Email address, which is shown as an image: skip it
}
# if file exists don't write headers row
csv_headers = not(Path(FACULTY_LIST_PATH).is_file())
for page_num in range(FIRST_PAGE or 1, LAST_PAGE + 1):  # loop through each page
    print(f'Page {page_num}/{LAST_PAGE} ...', end=' ')
    if not FIRST_PAGE:
        print('skipping (config)')
        continue

    try:
        page = req.get(url=BASE, params={'page': page_num}, headers=HEADERS)
        page.raise_for_status()
        rows = BeautifulSoup(page.text, 'html.parser') \
            .find('table', attrs=table_attrs) \
            .find('tbody') \
            .find_all('tr')
    except (AttributeError, req.HTTPError):  # table not found, go to next page
        print('error')
        continue

    for row in rows:  # each row contains the contact info of a faculty member
        parsed_row = {
            'Personal Website': None, 'Institution ID': None, 'Email': None}
        try:
            faculty_url = row.find('a', href=True)['href']
            parsed_row['Personal Website'] = faculty_url
            parsed_row['Institution ID'] = furl(faculty_url).path.segments[-1]
            parsed_row['Email'] = f'{parsed_row["Institution ID"]}@ut.ac.ir'
        except TypeError:
            pass

        columns = row.find_all('td')
        for column in columns:
            column_name_en = info_mapper[column['data-title']]
            if not column_name_en:
                continue
            parsed_row[column_name_en] = column.text \
                .strip().replace('\u200c', '')

        nullify(parsed_row)  # replace null like values (e.g. '---') with None
        exporter(FACULTY_LIST_PATH, [parsed_row], headers=csv_headers)
        csv_headers = False
    print('exported')


# ==============================================================================
# Step 2: Get additional data for each faculty (from Farsi & English pages)
# ==============================================================================


rows = get_row(FACULTY_LIST_PATH)
info_mapper = {
    'نام و نام خانوادگی': '',  # Full Name, which is already collected: skip it
    'پست الکترونیک': '',  # Email address, which is already collected: skip it
    'مرتبه علمی': '',  # Rank, which is already collected: skip it
    'آدرس محل کار': '',  # Office address, which is not needed: skip it
    'دانشکده/گروه': 'Department Fa',
    'تلفن محل کار': 'Office',
    'نمابر': 'Fax',
    'ادرس وب سایت': '',  # Personal Website, which is already collected: skip it
    'Full Name': 'Full Name En',
    'Email': '',
    'Academic Rank': 'Rank En',
    'Department': 'Department En',
    'Work phone': '',
    'Fax': '',
    'Website': '',
}
errors = []
# if file exists don't write headers row
csv_headers = not(Path(FACULTY_DETAILS_PATH).is_file())
first_faculty_crawled = not FIRST_FACULTY_ID or False  # no config => crawl all
for row in rows:
    if not row['Institution ID']:
        continue
    print(f'ID: {row["Institution ID"]} ...', end=' ')
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

    try:
        page_fa = req.get(
            url=row['Personal Website'],
            params={'lang': 'fa-ir'},
            allow_redirects=False,
            headers=HEADERS
        )
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

    try:  # faculty's general info
        general_info = soup \
            .find('div', attrs={'class': 'cv-info'}) \
            .find('table') \
            .find_all('tr')

        for item in general_info:
            # table columns format: [item_type, ':', item_content]
            columns = item.find_all('td')
            columns = [element.text.strip() for element in columns]
            column_name_en = info_mapper[columns[0]]
            if not column_name_en:
                continue
            row[column_name_en] = columns[2]
        print('General info done ...', end=' ')
    except AttributeError:
        print('General info error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': str(e), 'section': 'info',
            'id': row['Institution ID']})
        pass

    try:  # faculty's profile picture
        main_content = soup.find('div', attrs={'class': 'main-content'})
        row['Profile Picture URL'] = main_content \
            .find('div', attrs={'class': 'profile-pic'}) \
            .find('img', src=True)['src']
        print('Profile picture done ...', end=' ')
    except Exception as e:  # catchall
        print('Profile picture error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': str(e), 'section': 'pic',
            'id': row['Institution ID']})
        pass

    try:  # crawl the english page for general_info as well
        page_en = req.get(
            url=row['Personal Website'],
            params={'lang': 'en-gb'},
            allow_redirects=False,
            headers=HEADERS
        )
        page_en.raise_for_status()
        general_info = BeautifulSoup(page_en.text, 'html.parser') \
            .find('div', attrs={'class': 'cv-info'}) \
            .find('table') \
            .find_all('tr')

        for item in general_info:
            columns = item.find_all('td')
            columns = [element.text.strip() for element in columns]
            column_name_en = info_mapper[columns[0]]
            if not column_name_en:
                continue
            row[column_name_en] = columns[2]
        print('English page done ...', end=' ')
    except Exception as e:  # catchall
        print('English page error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': str(e), 'section': 'eng',
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
