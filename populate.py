import mysql.connector as mysql
import json
import os
import io
import csv
import random
from collections import OrderedDict
from datetime import datetime

with open('config.json', 'r') as read_file:
    client = json.load(read_file)

from wrapper import Database, country

# table_ids = {
#         'subject': {'order': 0, 'id': ['asjc_code']},
#         'country': {'order': 0, 'id': ['name']},

#         'source_subject': {'order': 1, 'id': ['source_id', 'subject_id']},

#         'keyword': {'order': 2, 'id': ['keyword_id']},
        
#         'paper_keyword': {'order': 3, 'id': ['paper_id', 'keyword_id']},
#     }

countries = []
with io.open('data\\Countries.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for row in reader:
       countries.append(row)

faculties = []
with io.open('data\\faculties.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for row in reader:
        if row['Scopus']:
            row['Scopus'] = list(map(int, row['Scopus'].split(',')))
        faculties.append(row)

asjc = []
with io.open('data\\ASJC Codes.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for row in reader:
        asjc.append(row)

sources = []
with io.open('data\\Scopus Sources.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    to_be_removed = [
        'Active', 'Discontinued', 'Coverage', '2016 CiteScore', '2017 CiteScore', '2018 CiteScore',
        'Medline-sourced', 'Open Access', 'Articles in Press Included', 'Added to list April 2019',
        'Title history indication', 'Related title to title history indication', 'Other related title 1',
        'Other related title 2', 'Other related title 3', 'Publisher imprints grouped to main Publisher',
    ]
    for row in reader:
        for col in to_be_removed:
            row.pop(col, None)
        row['ASJC'] = [int(code)
                       for code in row['ASJC'].split(';') if code != '']
        sources.append(row)

d2 = Database(config=client, db_name='scopus')

# for subject in asjc:
#     subject_info = {
#         'asjc_code': subject['Code'],
#         'top': subject['Top'],
#         'middle': subject['Middle'],
#         'low': subject['Low'],
#     }
    # print(subject)
    # server_response = d2._insert_one('subject', subject_info)
    # print(server_response)

# d2._update_one('subject', {'asjc_code': 3615, 'top': 'salam', 'low': 'bye'})

# for country in countries:
#     country_info = {
#         'name': country['name'],
#         'code': country['alpha-2'],
#         'region': country['region'],
#         'sub_region': country['sub-region']
#     }
#     server_response = d2._insert_one('country', country_info)


for cnt, source in enumerate(sources[:100]):
    source_info = {
        'source_id_scp': source['Source ID'],
        'publisher': source['Publisher'],
        'country': d2._read('country', search={'name': {'value': country(source['Country']), 'operator': '='}})[-1][0],
    }
    print(cnt)
    print(source_info)