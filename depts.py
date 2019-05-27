# ==============================================================================
# modules
# ==============================================================================

import os
import io
import csv
import json
from collections import OrderedDict

# ==============================================================================
# constants
# ==============================================================================

path = 'data\\Sharif University of Technology'
files = list(os.walk(path))[0][2]

# ==============================================================================
# import
# ==============================================================================

faculties = []
with io.open('data\\faculties.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for row in reader:
        if row['Scopus']:
            row['Scopus'] = [int(eval(auth_id)[0]) for auth_id in row['Scopus'].split(';')]
        faculties.append(row)

for file in files[0:1]:
    with io.open(os.path.join(path, file), 'r', encoding='utf8') as raw:
        data = json.load(raw)
    data = data['search-results']['entry']
    for paper in data:
        auth_ids = [auth['authid'] for auth in paper['author']]

# ==============================================================================
# class
# ==============================================================================

class Institution:
    
    count = 0
    ids=[]
    
    def __init__(self, affil_id: int, name='Sharif', alias=[]):
        if affil_id not in Institution.ids:
            self.id = affil_id
            Institution.ids.append(affil_id)
            self.name = name
            self.alias = alias
            self.depts = []
            Institution.count += 1
    
    def add_dept(self, dept):
        if dept not in self.depts:
            self.depts.append(dept)
    
    def get_all(self):
        return Institution.ids

class Department:
    
    count = 0
    
    def __init__(self, name, abbr, parent, alias=[]):
        self.name = name
        self.abbr = abbr
        self.parent = parent
        self.alias = alias
        self.authors = []
        self.faculties = []
        Department.count += 1
    
    def add_author(self, author):
        if author not in self.authors:
            self.authors.append(author)
            if (author.faculty) and (author not in self.faculties):
                self.faculties.append(author)

class Author:
    
    count = 0
    ids = []

    def __init__(self, auth_id, first, last, sex='', rank='', faculty=False):
        if auth_id not in Author.ids:
            self.id = auth_id
            self.first = first
            self.last = last
            self.faculty = faculty
            self.sex = sex
            self.rank = ''
            self.publications = []
            Author.count += 1
    
    def add_pub(self, publication):
        if publication not in self.publications:
            self.publications.append(publication)

class Publication:
    
    count = 0
    
    def __init__(self, publication_id, authors, title, year, journal):
        self.id = publication_id
        self.authors = authors
        self.title = title
        self.year = year
        self.journal = journal
        Publication.count += 1

        for auth in authors:
            # new author
            if auth['id'] not in Author.ids:
                pass
            else:
                pass


# ==============================================================================
# playground
# ==============================================================================

# data['search-results']['entry'][0]['author'][0]['authid']

# print(data[0])
publications = []
for pub in data[0:3]:
    publication_id = int(pub['dc:identifier'].split(':')[1])
    title = pub['dc:title']
    year = int(pub['prism:coverDate'].split('-')[0])
    journal = pub['prism:publicationName']
    authors = []

    publications.append(Publication(publication_id, authors, title, year, journal))

for pub in publications:
    print(pub.id)
    print(pub.authors)
    print(pub.title)
    print(pub.year)
    print(pub.journal)
    print('--------------')
print(Publication.count)