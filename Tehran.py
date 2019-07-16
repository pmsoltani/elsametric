#%%
import io
import csv
import copy
import requests as req
from bs4 import BeautifulSoup

base = 'https://ut.ac.ir/fa/faculty'
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
    page = req.get(url=base, params={'page': page_no})
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

#%%
# faculties_copy = copy.deepcopy(faculties)
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
for faculty in faculties_copy[1531:]:
    base = faculty['link']
    if not base:  # faculty page unknown
        continue

    try:
        page_fa = req.get(
            url=base, params={'lang': 'fa-ir'}, allow_redirects=False)
        soup = BeautifulSoup(page_fa.text, 'html.parser')
        rows = soup \
            .find('div', attrs={'class': 'cv-info'}) \
            .find('table') \
            .find_all('tr')

        for row in rows:
            columns = row.find_all('td')
            columns = [element.text.strip() for element in columns]
            faculty[english_keys[columns[0]]] = columns[2]
    except AttributeError:  # page not found
        continue
    except:  # catchall
        # errors.append({'type': str(type(e)), 'msg': str(e)})
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
        print('No EDU:  ', faculty['link'])

    page_en = req.get(
        url=base, params={'lang': 'fa-ir'}, allow_redirects=False)
    rows = BeautifulSoup(page_en.text, 'html.parser') \
        .find('div', attrs={'class': 'cv-info'}) \
        .find('table') \
        .find_all('tr')

    for row in rows:
        columns = row.find_all('td')
        columns = [element.text.strip() for element in columns]
        faculty[columns[0]] = columns[2]



#%%
file_name = 'tehran.csv'
with io.open(file_name, 'w', encoding='utf-8') as csv_file:
    w = csv.DictWriter(
        csv_file,
        faculties[0].keys(),
        delimiter=',',
        lineterminator='\n',
    )
    w.writerow(dict((fn, fn) for fn in faculties[0].keys()))
    w.writerows(faculties)


#%%
edu_keys = set()
for faculty in faculties_copy:
    cnt = 0
    for k in faculty.keys():
        if 'edu' in k:
            cnt += 1
    edu_keys.add(cnt)
print(max(edu_keys))


#%%
faculties_copy[806]

#%%
