#%%
import requests as req
from bs4 import BeautifulSoup

base = 'https://ut.ac.ir/fa/faculty'

faculties = []
for page_no in range(1, 107):
    params = {'page': page_no,}

    page = req.get(url=base, params=params)
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find(
        'table',
        attrs={'class': 'table table-striped table-bordered responsive-table'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')

    data = []
    english_keys = {
        'نام': 'first',
        'نام خانوادگی': 'last',
        'دانشکده/گروه': 'dept',
        'رتبه': 'rank',
        'پست الکترونیکی': 'email'
    }
    for row in rows:
        faculty_id = int(row['data-key'])
        link = row.find('a', href=True)['href']
        columns = row.find_all('td')
        parsed = {'faculty_id': faculty_id, 'link': link}
        for element in columns:
            parsed[english_keys[element['data-title']]] = element.text.strip()
        parsed['dept'] = parsed['dept'].replace('\u200c', '')
        data.append(parsed)

    faculties += data

faculties

#%%
