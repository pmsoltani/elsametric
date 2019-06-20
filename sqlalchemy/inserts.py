from base import Session, engine, Base

from paper import Paper
from keyword_ import Keyword
from fund import Fund
from source import Source
from subject import Subject
from country import Country

Base.metadata.create_all(engine)
session = Session()

import json
import os
import io
import csv
import random
import time
import winsound
from sys import getsizeof
from collections import OrderedDict
import datetime

start = time.time()
max_inserts = 1000
def session_manager():
    pass

def country_name(name: str):
    countries = {
        'Russian Federation': 'Russia',
        'USA': 'United States',
        'Great Britain': 'United Kingdom',
        'Vietnam': 'Viet Nam',
        'Zweden': 'Sweden',
        'Czech Republic': 'Czechia',
    }
    if name in countries.keys():
        return countries[name]
    return name

frequency = 2000  # Set Frequency (Hz)
duration = 300  # Set Duration (ms)
# winsound.Beep(frequency=frequency, duration=duration)

countries = []
with io.open('countries.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for row in reader:
        country = Country(
            name=row['name'], domain=row['domain'],
            region=row['region'], sub_region=row['sub_region']
        )
        query = session.query(Country) \
            .filter(Country.name == country.name) \
            .first()
        if query:
            continue
        session.add(country)
        countries.append(country)

session.commit()

subjects = []
with io.open('subjects.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for row in reader:
        subject = Subject(
            asjc=row['asjc'],
            top=row['top'], middle=row['middle'], low=row['low']
        )
        query = session.query(Subject) \
            .filter(Subject.asjc == subject.asjc) \
            .first()
        if query:
            continue
        session.add(subject)
        subjects.append(subject)

session.commit()

# sources = []
with io.open('sources.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for cnt, row in enumerate(reader):
        for item in row:
            if not row[item]:
                row[item] = None
        source = Source(
            id_scp=row['id_scp'], title=row['title'], type=row['type'],
            issn=row['issn'], e_issn=row['e_issn'], publisher=row['publisher']
        )
        query = session.query(Source) \
            .filter(Source.id_scp == source.id_scp) \
            .first()
        if query:
            continue
        country = country_name(row['country'])
        if country:
            query = session.query(Country) \
                .filter(Country.name == country) \
                .first()
            source.country = query
        if row['asjc']:
            subject_codes = [int(code) 
                           for code in row['asjc'].split(';') if code != '']
            for code in subject_codes:
                query = session.query(Subject) \
                    .filter(Subject.asjc == code) \
                    .first()
                if query:
                    source.subjects.append(query)

        session.add(source)
        # sources.append(source)
        if (cnt + 1) % max_inserts == 0:
            session.commit()
            # sources = []
        
try:
    session.commit()
except:
    print('nothing to commit')
finally:
    session.close()

end = time.time()

print(f'countries: {getsizeof(countries)}, len: {len(countries)}')
print(f'subjects: {getsizeof(subjects)}, len: {len(subjects)}')
# print(f'sources: {getsizeof(sources)}, len: {len(sources)}')
print(f'operation time: {str(datetime.timedelta(seconds=(end - start)))}')

sources = session.query(Source) \
    .all()

print()
print(len(sources))
print(sources[0])
print(0, source[0].title)
print(100, sources[100].title)
# session.close()