# %%
import io
import csv
import json
import requests as req
from bs4 import BeautifulSoup
from furl import furl
from pathlib import Path
from helpers import get_row, exporter, nullify

# %%
# ==============================================================================
# Config
# ==============================================================================

CURRENT_DIR = Path.cwd()
with io.open(CURRENT_DIR / 'config.json', 'r') as config_file:
    config = json.load(config_file)

config = config['crawlers']['University of Tehran']
DATA_PATH = config['data_directory']
FACULTY_LIST = config['faculties_list']
FACULTY_DETAILS = config['faculties_details']
ERRORS_LOG = config['errors_log']
BASE = config['base_url']
FIRST_PAGE = config['first_page']
FIRST_FACULTY_ID = config["first_faculty_id"]

AGT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'
HEADERS = {'User-Agent': AGT}

fa_en_mapper = {
    'نام': 'First Fa',
    'نام خانوادگی': 'Last Fa',
    'دانشکده/گروه': 'Department Full Fa',
    'رتبه': 'Rank Fa',
    'پست الکترونیکی': 'Email'
}
table_attrs = {'class': 'table table-striped table-bordered responsive-table'}

try:
    page = req.get(url=BASE, headers=HEADERS)
    soup = BeautifulSoup(page.text, 'html.parser')
    last_page_url = soup \
        .find('ul', attrs={'class': 'pagination'}) \
        .find('li', attrs={'class': 'last'}) \
        .find('a')['href']
    LAST_PAGE = int(furl(last_page_url).args['page'])
except AttributeError:
    LAST_PAGE = 106  # hardcoded value


# %%
# ==============================================================================
# Get a list of all faculties
# ==============================================================================


# loop through each page that contains a table of faculty names
csv_headers = True
for page_number in range(FIRST_PAGE or 1, LAST_PAGE + 1):
    print(f'Page {page_number}/{LAST_PAGE} ...', end=' ')
    if not FIRST_PAGE:
        print('skipping (config)')
        continue
    page = req.get(url=BASE, params={'page': page_number}, headers=HEADERS)
    soup = BeautifulSoup(page.text, 'html.parser')
    try:
        rows = soup \
            .find('table', attrs=table_attrs) \
            .find('tbody') \
            .find_all('tr')
        # each row contains the contact info of a faculty member
    except AttributeError:  # table not found, move to the next page
        print('error')
        continue

    for row in rows:
        # 'data-key' is an integer assigned to each faculty memeber
        faculty_key = int(row['data-key'])
        try:
            # link to the faculty's profile page
            faculty_link = row.find('a', href=True)['href']
            faculty_id = furl(faculty_link).path.segments[-1]
            faculty_email = f'{faculty_id}@ut.ac.ir'
        except TypeError as e:
            faculty_link = None
            faculty_email = None

        parsed_row = {}

        columns = row.find_all('td')
        for column in columns:
            column_name_fa = column['data-title']
            column_name_en = fa_en_mapper[column_name_fa]
            parsed_row[column_name_en] = column.text.strip()
        parsed_row['Department Full Fa'] = parsed_row['Department Full Fa'] \
            .replace('\u200c', '')

        parsed_row = {
            **parsed_row,
            'Institution Key': faculty_key,
            'Personal Website': faculty_link,
            'Institution ID': faculty_id,
            'Email': faculty_email
        }
        nullify(parsed_row)

        # write each row to the file asap
        exporter(
            CURRENT_DIR / DATA_PATH / FACULTY_LIST,
            [parsed_row],
            headers=csv_headers
        )
        csv_headers = False
    print('exported')


# %%
# ==============================================================================
# Get additional data for each faculty member
# ==============================================================================


rows = get_row(CURRENT_DIR / DATA_PATH / FACULTY_LIST)
fa_en_mapper = {
    'نام و نام خانوادگی': 'Full Name Fa',
    'پست الکترونیک': 'Email Fa',
    'مرتبه علمی': 'Rank Fa 2',
    'آدرس محل کار': 'Address Fa',
    'دانشکده/گروه': 'Department Fa',
    'تلفن محل کار': 'Office Fa',
    'نمابر': 'Fax Fa',
    'ادرس وب سایت': 'Personal Website Fa',
}
errors = []
csv_headers = True
first_faculty_crawled = not FIRST_FACULTY_ID or False
for row in rows:
    if not row['Institution ID']:
        continue
    print(f'ID: {row["Institution ID"]} ...', end=' ')
    if row['Institution ID'] == FIRST_FACULTY_ID:
        first_faculty_crawled = True
    if not first_faculty_crawled:
        print('skipping (config)')
        continue
    if not row['Personal Website']:  # faculty page not available
        print('error (page not available) ...', end=' ')
        exporter(
            CURRENT_DIR / DATA_PATH / FACULTY_DETAILS,
            [row],
            headers=csv_headers
        )
        print('exported')
        continue

    try:
        page_fa = req.get(
            url=row['Personal Website'],
            params={'lang': 'fa-ir'},
            allow_redirects=False,
            headers=HEADERS
        )
        soup = BeautifulSoup(page_fa.text, 'html.parser')
        general_info = soup \
            .find('div', attrs={'class': 'cv-info'}) \
            .find('table') \
            .find_all('tr')

        for item in general_info:
            # table format:
            # col0 -> item_type
            # col1 -> ':' (just a colon)
            # col2 -> item_content
            columns = item.find_all('td')
            columns = [element.text.strip() for element in columns]
            column_name_fa = columns[0]
            column_name_en = fa_en_mapper[column_name_fa]
            if 'Email' in column_name_en:
                continue
            row[column_name_en] = columns[2]

        main_content = soup.find('div', attrs={'class': 'main-content'})
        pic = main_content \
            .find('div', attrs={'class': 'profile-pic'}) \
            .find('img', src=True)['src']
        row['Profile Picture URL'] = pic
        print('Farsi page done ...', end=' ')
    except Exception as e:  # catchall
        print('Farsi page error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': str(e), 'section': 'fa',
            'id': row['Institution ID']})
        pass

    try:  # crawl the english page for general_info as well
        page_en = req.get(
            url=row['Personal Website'], params={'lang': 'en-gb'},
            allow_redirects=False, headers=HEADERS)
        general_info = BeautifulSoup(page_en.text, 'html.parser') \
            .find('div', attrs={'class': 'cv-info'}) \
            .find('table') \
            .find_all('tr')

        for item in general_info:
            columns = item.find_all('td')
            columns = [element.text.strip() for element in columns]
            column_name_en = columns[0]
            if 'Email' in column_name_en:
                continue
            row[column_name_en] = columns[2]
        print('English page done ...', end=' ')
    except Exception as e:  # catchall
        print('English page error ...', end=' ')
        errors.append({
            'type': str(type(e)), 'msg': str(e), 'section': 'en',
            'id': row['Institution ID']})
        pass

    nullify(row)
    exporter(
        CURRENT_DIR / DATA_PATH / FACULTY_DETAILS,
        [row],
        headers=csv_headers
    )
    csv_headers = False
    print('exported')

if errors:
    exporter(CURRENT_DIR / DATA_PATH / ERRORS_LOG, errors, all_rows=True)
    print()
    print('error logs exported')
