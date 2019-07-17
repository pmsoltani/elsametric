#%%
import io
import csv
import copy
import requests as req
from bs4 import BeautifulSoup

base = 'https://ut.ac.ir/fa/faculty'
agt = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'
headers = {'User-Agent': agt}

english_keys = {
    'نام': 'first',
    'نام خانوادگی': 'last',
    'دانشکده/گروه': 'full_dept',
    'رتبه': 'rank',
    'پست الکترونیکی': 'email'
}
table_attrs = {'class': 'table table-striped table-bordered responsive-table'}
first_page = 1
last_page = 106

#%%
faculties = []
for page_no in range(first_page, last_page + 1):
    page = req.get(url=base, params={'page': page_no}, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find('table', attrs=table_attrs)
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')

    data = []
    for row in rows:
        faculty_id = int(row['data-key'])
        try:
            faculty_link = row.find('a', href=True)['href']
            faculty_email = faculty_link.split('/')[-1] + '@ut.ac.ir'
        except TypeError:
            faculty_link = None
            faculty_email = None

        parsed = {'faculty_id': faculty_id, 'link': faculty_link}

        columns = row.find_all('td')
        for element in columns:
            parsed[english_keys[element['data-title']]] = element.text.strip()

        parsed['email'] = faculty_email
        parsed['full_dept'] = parsed['full_dept'].replace('\u200c', '')
        data.append(parsed)

    faculties += data

file_name = 'tehran_initial.csv'
with io.open(file_name, 'w', encoding='utf-8') as csv_file:
    writer = csv.DictWriter(
        csv_file, faculties[0].keys(), delimiter=',', lineterminator='\n')
    writer.writerow(dict((fn, fn) for fn in faculties[0].keys()))
    writer.writerows(faculties)

#%%
# file_name = 'tehran_initial.csv'
faculties = []
with io.open(file_name, 'r', encoding='utf-8') as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        faculties.append(row)

english_keys = {
    'نام و نام خانوادگی': 'full_name_fa',
    'پست الکترونیک': 'email2_fa',
    'مرتبه علمی': 'rank_fa',
    'آدرس محل کار': 'office_fa',
    'دانشکده/گروه': 'dept_fa',
    'تلفن محل کار': 'phone_fa',
    'نمابر': 'fax_fa',
    'ادرس وب سایت': 'page_fa',
}
errors = []
for faculty in faculties:
    if not faculty['link']:  # faculty page unknown
        continue

    print(faculty['link'].split('/')[-1])
    try:
        page_fa = req.get(
            url=faculty['link'], params={'lang': 'fa-ir'},
            allow_redirects=False, headers=headers)
        soup = BeautifulSoup(page_fa.text, 'html.parser')
        rows = soup \
            .find('div', attrs={'class': 'cv-info'}) \
            .find('table') \
            .find_all('tr')

        for row in rows:
            columns = row.find_all('td')
            columns = [element.text.strip() for element in columns]
            faculty[english_keys[columns[0]]] = columns[2]
    except Exception as e:  # catchall
        errors.append({
            'type': str(type(e)), 'msg': str(e), 'section': 'fa',
            'id': faculty['faculty_id']})
        continue


    main_content = soup.find('div', attrs={'class': 'main-content'})
    pic = main_content \
        .find('div', attrs={'class': 'profile-pic'}) \
        .find('img', src=True)['src']
    faculty['pic'] = pic

    try:
        edu = main_content \
            .find('div', attrs={'id': 'activity-1'}) \
            .find_all('li')

        for cnt, item in enumerate(edu):
            faculty[f'edu{cnt}'] = item.text.strip()
    except AttributeError:
        errors.append({
            'type': str(AttributeError), 'msg': None, 'section': 'edu',
            'id': faculty['faculty_id']})

    try:
        page_en = req.get(
            url=faculty['link'], params={'lang': 'en-gb'},
            allow_redirects=False, headers=headers)
        rows = BeautifulSoup(page_en.text, 'html.parser') \
            .find('div', attrs={'class': 'cv-info'}) \
            .find('table') \
            .find_all('tr')

        for row in rows:
            columns = row.find_all('td')
            columns = [element.text.strip() for element in columns]
            faculty[columns[0]] = columns[2]
    except Exception as e:  # catchall
        errors.append({
            'type': str(type(e)), 'msg': str(e), 'section': 'en',
            'id': faculty['faculty_id']})
        continue

#%%
max_edu = 0
for faculty in faculties:
    cnt = 0
    for k in faculty.keys():
        if 'edu' in k:
            cnt += 1
    max_edu = max(max_edu, cnt)

for faculty in faculties:
    keys = faculty.keys()
    for cnt in range(max_edu):
        edu = f'edu{cnt}'
        if edu not in keys:
            faculty[edu] = None

file_name = 'tehran_final.csv'
with io.open(file_name, 'w', encoding='utf-8') as csv_file:
    writer = csv.DictWriter(
        csv_file, faculties[0].keys(), delimiter=',', lineterminator='\n')
    writer.writerow(dict((fn, fn) for fn in faculties[0].keys()))
    writer.writerows(faculties)

#%%
