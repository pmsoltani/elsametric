#%%
import io
import csv
import requests as req
from bs4 import BeautifulSoup

base = 'http://www.modares.ac.ir/pro/academic_staff/vanaki_z'
agt = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'
headers = {'User-Agent': agt}

page = req.get(base, headers=headers)
soup = BeautifulSoup(page.content, 'html.parser')

#%%
faculties = []
parsed = {}
side_bar = soup.find('div', attrs={'id': 'sidebar'})
profile = side_bar.find('div', attrs={'id': 'profile'})
pic = 'http://www.modares.ac.ir' + profile.find('img', src=True)['src']
name = profile.find('h2').text.strip()
try:
    rank = profile.find('h3').text.strip()
except:
    rank = None
parsed = {'name': name, 'pic': pic, 'rank': rank}

#%%
header = soup.find('div', attrs={'class': 'pageheader'})
title = header.find('h3').text.strip()
in_office = header.find('div', attrs={'class': 'row'}).find(
    'span').text.strip()[1:-1]
in_office
parsed['title'] = title
parsed['in_office'] = in_office

#%%
icon_keys = {
    'fa-envelope': 'email',
    'fa-phone': 'phone',
    'fa-fax': 'fax',
    'fa-link': 'page_en',
    'fa-line-chart': 'scientometrics',
    'fa-globe': 'scopus',
    'fa-google': 'google',
}
content = soup.find('div', attrs={'class': 'pagecontents'})
contact = content.find('div', attrs={'class': 'row'}).find(
    'div', attrs={'class': 'col-md-5'}).find_all('li')
for item in contact:
    try:
        key = icon_keys[item.find('i')['class'][1]]
        if key in ['email', 'phone', 'fax']:
            parsed[key] = item.text.strip()
        else:
            parsed[key] = item.find('a', href=True)['href']
    except KeyError:
        parsed[item.find('i')['class'][1]] = item.find('a', href=True)['href']
    except Exception as e:
        continue

#%%
info = content.find('div', attrs={'class': 'row'}).find(
    'div', attrs={'class': 'col-md-7'})
edu = info.find('div', attrs={'id': 'educ'}).find_all('li')
for cnt, degree in enumerate(edu):
    degree_string = degree.find('span', attrs={'class': 'degree'}).text.strip()
    degree_string = degree_string.replace('(', '').replace(')', '')
    year = degree_string[-4:].strip()
    degree_type = degree_string[:-4].strip()

    major = degree.find('p', attrs={'class': 'waht'}).text.strip()
    uni = degree.find('p', attrs={'class': 'where'}).text.strip()
    parsed[f'edu{cnt}'] = f'{degree_type}, {year}, {major}, {uni}'

interests = [subject.text.strip() for subject in info.find(
    'div', attrs={'id': 're'}).find_all('li')]
parsed['interests'] = ', '.join(interests)
