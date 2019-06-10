import mysql.connector as mysql
import json
import os
import io
import csv
import random
import time
import winsound
from collections import OrderedDict
from datetime import datetime
from wrapper import Database, country_name, data_inspector, strip

frequency = 2500  # Set Frequency To 2500 Hertz
duration = 300  # Set Duration To 1000 ms == 1 second

with open('config.json', 'r') as read_file:
    client = json.load(read_file)

start = time.time()
d2 = Database(config=client, db_name='scopus2')

# print()
# print('----------------------')
# print()

# countries = []
# with io.open('data\\Countries.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for row in reader:
#        countries.append(row)
# for country in countries:
#     country_info = {
#         'name': country['name'],
#         'code': country['alpha-2'],
#         'region': country['region'],
#         'sub_region': country['sub-region']
#     }
#     server_response = d2._insert_one('country', country_info)
#     print(server_response)

# print()
# print('----------------------')
# print()

# subjects = []
# with io.open('data\\ASJC Codes.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for row in reader:
#         subjects.append(row)
# for subject in subjects:
#     subject_info = {
#         'asjc_code': subject['Code'],
#         'top': subject['Top'],
#         'middle': subject['Middle'],
#         'low': subject['Low'],
#     }
#     server_response = d2._insert_one('subject', subject_info)
#     print(server_response)

# print()
# print('----------------------')
# print()

def retriever(data, key: str):
    if key not in data.keys():
        return None
    if not data[key]:
        return None
    return data[key]

# sources = []
# with io.open('data\\Scopus Journals.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     to_be_removed = [
#         'Active', 'Discontinued', 'Coverage', '2016 CiteScore', '2017 CiteScore', '2018 CiteScore',
#         'Medline-sourced', 'Open Access', 'Articles in Press Included', 'Added to list April 2019',
#         'Title history indication', 'Related title to title history indication', 'Other related title 1',
#         'Other related title 2', 'Other related title 3', 'Publisher imprints grouped to main Publisher',
#     ]
#     for row in reader:
#         for col in to_be_removed:
#             row.pop(col, None)
#         row['ASJC'] = [int(code)
#                        for code in row['ASJC'].split(';') if code != '']
#         sources.append(row)
# for cnt, source in enumerate(sources):
#     source_id_scp = int(source['Source ID'])
#     source_data = d2._read(
#         table_name='source',
#         search={'source_id_scp': {'value': source_id_scp, 'operator': '='}},
#         result_columns=True
#     )['value']
#     if source_data:
#         country = retriever(source, 'Country')
#         country_id = None
#         if country:
#             country_id = d2._read(
#                 table_name='country',
#                 search={'name': {'value': country_name(country), 'operator': '='}}
#             )['value']
#             if country_id:
#                 country_id = country_id[-1][0]
#         source_info = {
#             'source_id_scp': source_id_scp,
#             'title': retriever(source, 'Source Title'),
#             'url': f'https://www.scopus.com/sourceid/{source_id_scp}',
#             'type': retriever(source, 'Source Type'),
#             'issn': retriever(source, 'ISSN'),
#             'e_issn': retriever(source, 'E_ISSN'),
#             'publisher': strip(data=retriever(source, 'Publisher'), max_length=45, accepted_chars=''),
#             'country_id': country_id
#         }
#         source_id = d2._update_one('source', source_info, null_scape=True)
#         print(source_id)
#         source_id = source_id['value']
#         for asjc in source['ASJC']:
#             subject_id = d2._read(
#                 table_name='subject',
#                 search={'asjc_code': {'value': asjc, 'operator': '='}}
#             )['value']
#             if subject_id:
#                 subject_id = subject_id[-1][0]
#             source_subject_info = {
#                 'source_id': source_id,
#                 'subject_id': subject_id
#             }
#             server_response = d2._insert_one('source_subject', source_subject_info)
#             print(server_response)

# print()
# print('----------------------')
# print()

# sources = []
# with io.open('data\\Scopus Conferences.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     to_be_removed = [
#         'Discontinued', 'Coverage', '2016 CiteScore', '2016 SJR', '2016 SNIP', 
#         '2017 CiteScore', '2017 SJR', '2017 SNIP', '2018 CiteScore', '2018 SJR', '2018 SNIP',
#     ]
#     for row in reader:
#         for col in to_be_removed:
#             row.pop(col, None)
#         if row['ASJC']:
#             row['ASJC'] = [int(code) for code in row['ASJC'].split(';') if code != '']
#         else:
#             row['ASJC'] = []
#         sources.append(row)
# for cnt, source in enumerate(sources):
#     source_id_scp = int(source['Source ID'])
#     source_data = d2._read(
#         table_name='source',
#         search={'source_id_scp': {'value': source_id_scp, 'operator': '='}},
#         result_columns=True
#     )['value']
#     if source_data:
#         source_info = {
#             'source_id_scp': source_id_scp,
#             'title': strip(data=retriever(source, 'Source title'), max_length=512, accepted_chars=''),
#             'url': None,
#             'type': retriever(source, 'Source Type'),
#             'issn': retriever(source, 'ISSN'),
#             'e_issn': retriever(source, 'E_ISSN'),
#             'publisher': strip(data=retriever(source, 'Publisher'), max_length=45, accepted_chars=''),
#             'country_id': None
#         }
#         source_id = d2._update_one('source', source_info, null_scape=True)
#         source_id = source_id['value']
#         if source['ASJC']:
#             for asjc in source['ASJC']:
#                 subject_id = d2._read(
#                     table_name='subject',
#                     search={'asjc_code': {'value': asjc, 'operator': '='}}
#                 )['value']
#                 if subject_id:
#                     subject_id = subject_id[-1][0]
#                 source_subject_info = {
#                     'source_id': source_id,
#                     'subject_id': subject_id
#                 }
#                 server_response = d2._insert_one('source_subject', source_subject_info)
#                 print(server_response)

# print()
# print('----------------------')
# print()

# print('-----------------------------------------------------------------------')
# paper_cnt = 0
# skipped_cnt = 0

# path = 'data\\Sharif University of Technology'
# files = list(os.walk(path))[0][2]

# for file in files:
#     with io.open(os.path.join(path, file), 'r', encoding='utf8') as raw:
#         data = json.load(raw)
#     data = data['search-results']['entry']
#     ret_time = datetime.utcfromtimestamp(
#         int(file.split('.')[0].split('_')[-1])).strftime('%Y-%m-%d %H:%M:%S')
#     for paper in data:
#         warnings = data_inspector(paper)
#         print(file)
#         print(paper['dc:identifier'])
#         try:
#             ins_id = d2.raw_insert(paper, retrieval_time=ret_time, country_data=True)
#             print(ins_id)
#             paper_cnt += 1
#             if not ins_id['value']:
#                 skipped_cnt += 1
#             print('---------------------')
#         except Exception as e:
#             winsound.Beep(frequency, duration)
#             print(e)
# d2._close()
# print()
# print()
# print(f'{len(files)} file reviewed')
# print(f'{paper_cnt} papers reviewed')
# print(f'{skipped_cnt} papers skipped')
# print(f'{paper_cnt - skipped_cnt} papers inserted into the db')

# print('-----------------------------------------------------------------------')

# departments = []
# with io.open('data\\departments.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for row in reader:
#         row['institution_id_scp'] = 60027666
#         departments.append(row)
# for department in departments:
#     institution_id = d2._read(
#         table_name='institution',
#         search={'institution_id_scp': {'value': department['institution_id_scp'], 'operator': '='}}
#     )['value']
#     if institution_id:
#         institution_id = institution_id[-1][0]
    
#     department_info = {
#         'institution_id': institution_id,
#         'name': department['Full Name'],
#         'abbreviation': department['Abbreviation'],
#         'type': department['Type'],
#     }
#     server_response = d2._insert_one('department', department_info)
#     print(server_response)

# profs = []
# with io.open('data\\faculties.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for row in reader:
#         if row['Scopus']:
#             row['Scopus'] = [int(scp_id) for scp_id in row['Scopus'].split(',')][0]
#         row['Departments'] = [dept.strip() for dept in row['Departments'].split(',')]
#         if row['Sex'] == 'M':
#             row['Sex'] = 1
#         else:
#             row['Sex'] = 0
#         profs.append(row)
# for prof in profs:
#     author_info = {
#         'author_id_scp': prof['Scopus'],
#         'sex': prof['Sex'],
#         'type': 'Faculty',
#         'rank': prof['Rank']
#     }
#     author_id = d2._update_one('author', author_info)['value']
#     if author_id:
#         institution_id = d2._read(
#             table_name='institution',
#             search={'institution_id_scp': {'value': 60027666, 'operator': '='}}
#         )['value']
#         if institution_id:
#             institution_id = institution_id[-1][0]
#         for dept in prof['Departments']:
#             department_id = d2._read(
#                 table_name='department',
#                 search={
#                     'abbreviation': {'value': dept, 'operator': '='},
#                     'institution_id': {'value': institution_id, 'operator': '='}
#                 }
#             )['value']
#             if department_id:
#                 department_id = department_id[-1][0]
#             author_department_info = {
#                 'author_id': author_id,
#                 'department_id': department_id,
#                 'institution_id': institution_id
#             }
#             server_response = d2._insert_one('author_department', author_department_info)
#             print(server_response)

end = time.time()
print(f'Total time: {end - start} seconds')