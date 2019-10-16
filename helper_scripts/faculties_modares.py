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
config = config['crawlers']['Tarbiat Modares University']

DATA_PATH = CURRENT_DIR / config['data_directory']
FACULTY_LIST_PATH = DATA_PATH / config['faculties_list']
FACULTY_DETAILS_PATH = DATA_PATH / config['faculties_details']
ERRORS_LOG_PATH = DATA_PATH / config['errors_log']
BASE = config['base_url']
FIRST_PAGE = config['first_page']
FIRST_FACULTY_ID = config["first_faculty_id"]

AGT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'
HEADERS = {'User-Agent': AGT}


# %%
# ==============================================================================
# Step 1: Load the base page and crawl the Farsi alphabet
# ==============================================================================


page = req.get(url=BASE, headers=HEADERS)
alphabet = BeautifulSoup(page.text, 'html.parser') \
    .find('div', attrs={'class': 'alphanets'}) \
    .find_all('button')
alphabet = [letter.text for letter in alphabet]


# %%
# ==============================================================================
# Step 2: Get a list of faculties for each alphabet letter and export them
# ==============================================================================


BASE_FACULTY_LIST = 'http://www.modares.ac.ir/includes/services.jsp'
first_time = True
for letter in alphabet:
    print(letter)
    page = req.get(url=BASE_FACULTY_LIST, headers=HEADERS,
                   params={'serviceid': 792, 'k': letter})  # hard-coded value
    raw_faculties = BeautifulSoup(page.text, 'html.parser').find_all('a')
    parsed_faculties = []
    for faculty in raw_faculties:
        faculty_id = furl(faculty['href']).path.segments[-1]
        parsed_faculties.append({
            'Full Name Fa': faculty.text,
            'Institution ID': faculty_id,
            'Personal Website': furl(BASE).add(path=faculty_id).url,
            'Email': f'{faculty_id}@{furl(BASE).host.replace("www.","")}'
        })
    exporter(FACULTY_LIST_PATH, parsed_faculties,
             reset=first_time, bulk=True, headers=first_time)
    first_time = False


# ==============================================================================
# Step 3: Crawl the 'Personal Website' of each faculty and export the results
# ==============================================================================
# #%%
# faculties = []
# parsed = {}
# side_bar = soup.find('div', attrs={'id': 'sidebar'})
# profile = side_bar.find('div', attrs={'id': 'profile'})
# pic = 'http://www.modares.ac.ir' + profile.find('img', src=True)['src']
# name = profile.find('h2').text.strip()
# try:
#     rank = profile.find('h3').text.strip()
# except:
#     rank = None
# parsed = {'name': name, 'pic': pic, 'rank': rank}

# #%%
# header = soup.find('div', attrs={'class': 'pageheader'})
# title = header.find('h3').text.strip()
# in_office = header.find('div', attrs={'class': 'row'}).find(
#     'span').text.strip()[1:-1]
# in_office
# parsed['title'] = title
# parsed['in_office'] = in_office

# #%%
# icon_keys = {
#     'fa-envelope': 'email',
#     'fa-phone': 'phone',
#     'fa-fax': 'fax',
#     'fa-link': 'page_en',
#     'fa-line-chart': 'scientometrics',
#     'fa-globe': 'scopus',
#     'fa-google': 'google',
# }
# content = soup.find('div', attrs={'class': 'pagecontents'})
# contact = content.find('div', attrs={'class': 'row'}).find(
#     'div', attrs={'class': 'col-md-5'}).find_all('li')
# for item in contact:
#     try:
#         key = icon_keys[item.find('i')['class'][1]]
#         if key in ['email', 'phone', 'fax']:
#             parsed[key] = item.text.strip()
#         else:
#             parsed[key] = item.find('a', href=True)['href']
#     except KeyError:
#         parsed[item.find('i')['class'][1]] = item.find('a', href=True)['href']
#     except Exception as e:
#         continue

# #%%
# info = content.find('div', attrs={'class': 'row'}).find(
#     'div', attrs={'class': 'col-md-7'})
# edu = info.find('div', attrs={'id': 'educ'}).find_all('li')
# for cnt, degree in enumerate(edu):
#     degree_string = degree.find('span', attrs={'class': 'degree'}).text.strip()
#     degree_string = degree_string.replace('(', '').replace(')', '')
#     year = degree_string[-4:].strip()
#     degree_type = degree_string[:-4].strip()

#     major = degree.find('p', attrs={'class': 'waht'}).text.strip()
#     uni = degree.find('p', attrs={'class': 'where'}).text.strip()
#     parsed[f'edu{cnt}'] = f'{degree_type}, {year}, {major}, {uni}'

# interests = [subject.text.strip() for subject in info.find(
#     'div', attrs={'id': 're'}).find_all('li')]
# parsed['interests'] = ', '.join(interests)
