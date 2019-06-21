# external
# countries = []
# with io.open('countries.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for row in reader:
#         country = Country(
#             name=row['name'], domain=row['domain'],
#             region=row['region'], sub_region=row['sub_region']
#         )
#         query = session.query(Country) \
#             .filter(Country.name == country.name) \
#             .first()
#         if query:
#             continue
#         session.add(country)
#         countries.append(country)

# session.commit()

# subjects = []
# with io.open('subjects.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for row in reader:
#         subject = Subject(
#             asjc=row['asjc'],
#             top=row['top'], middle=row['middle'], low=row['low']
#         )
#         query = session.query(Subject) \
#             .filter(Subject.asjc == subject.asjc) \
#             .first()
#         if query:
#             continue
#         session.add(subject)
#         subjects.append(subject)

# session.commit()

# with io.open('sources.csv', 'r', encoding='utf-8-sig') as csvFile:
#     reader = csv.DictReader(csvFile)
#     for cnt, row in enumerate(reader):
#         for item in row:
#             if not row[item]:
#                 row[item] = None
#         source = Source(
#             id_scp=row['id_scp'], title=row['title'], type=row['type'],
#             issn=row['issn'], e_issn=row['e_issn'], publisher=row['publisher']
#         )
#         query = session.query(Source) \
#             .filter(Source.id_scp == source.id_scp) \
#             .first()
#         if query:
#             continue
#         country = country_name(row['country'])
#         if country:
#             query = session.query(Country) \
#                 .filter(Country.name == country) \
#                 .first()
#             source.country = query
#         if row['asjc']:
#             subject_codes = [int(code) 
#                            for code in row['asjc'].split(';') if code != '']
#             for code in subject_codes:
#                 query = session.query(Subject) \
#                     .filter(Subject.asjc == code) \
#                     .first()
#                 if query:
#                     source.subjects.append(query)

#         session.add(source)
#         # sources.append(source)
#         if (cnt + 1) % max_inserts == 0:
#             session.commit()
#             # sources = []
        
# try:
#     session.commit()
# except:
#     print('nothing to commit')
# finally:
#     session.close()


# author
# for auth in entry['author']:
#     keys = auth.keys()
#     author_id_scp = int(auth['authid'])
#     paper_author = Paper_Author(int(auth['@seq']))
#     author = session.query(Author) \
#         .filter(Author.id_scp == author_id_scp) \
#         .first()
#     if not author:
#         author = Author(
#             id_scp=author_id_scp,
#             first=key_get(auth, keys, 'given-name'),
#             last=key_get(auth, keys, 'surname'),
#             initials=key_get(auth, keys, 'initials')
#         )

#         author_profile = Author_Profile(
#             address=f'https://www.scopus.com/authid/detail.uri?authorId={author_id_scp}',
#             type='Scopus Profile',
#         )
#         author.profiles.append(author_profile)
#         session.add(author)
#         session.commit()
    
#     paper_author.author = author
#     session.add(paper_author)
#     print('//////////////')
#     print(paper_author.paper_id, paper_author.author_id, paper_author.author_no)
#     print(paper.authors)
#     print('//////////////')
#     paper.authors.append(paper_author)
#     print('Linked.')
#     print()
# print(f'ALL AUTHORS: {[[a.author.last, a.author.id] for a in paper.authors]}')

def data_inspector(data:dict):
    warnings = []
    top_keys = [
        'source-id', 'prism:publicationName', 'prism:coverDate',
        'dc:identifier', 'eid', 'dc:title', 'subtype', 'author-count',
        'openaccess', 'citedby-count', 'link',
        'author', 'affiliation',
    ]
    author_keys = ['authid', '@seq', 'afid']
    affiliation_keys = ['afid', 'affilname']

    keys = data.keys()
    for key in top_keys:
        if key not in keys:
            warnings.append(key)
    if 'link' not in warnings:
        if all(link['@ref'] != 'scopus' for link in data['link']):
            warnings.append('paper url')
    if 'author' not in warnings:
        for author in data['author']:
            keys = author.keys()
            for key in author_keys:
                if key not in keys:
                    warnings.append(f'author:{key}')
    if 'affiliation' not in warnings:
        for affiliation in data['affiliation']:
            keys = affiliation.keys()
            for key in affiliation_keys:
                if key not in keys:
                    warnings.append(f'affiliation:{key}')
    return warnings


def key_get(data:dict, keys, key:str, many:bool=False):
    if key in keys:
        result = data[key]
    else:
        result = None
    
    if type(result) == list:
        if not many:
            return result[0]['$']
        return [int(item['$']) for item in result]
    if type(result) == dict:
        return result['$']
    return result


def strip(data, max_length:int=8, accepted_chars:str='0123456789xX', force_strip:bool=True):
    if not data:
        return data
    if not accepted_chars:
        return data.strip()[:max_length]
    if force_strip:
        return ''.join([char for char in data if char in accepted_chars])[:max_length]
    return ''.join([char for char in data if char in accepted_chars])


def country_name(name:str):
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

def raw_insert(data:dict, retrieval_time, title_length=300, country_data=False):
        
        author_institution = []
        inst_from_author = []
        paper_author_info = []
        for author in data['author']:
            keys = author.keys()
            author_id_scp = int(author['authid'])
            author_info = {
                'author_id_scp': author_id_scp,
                'first': key_get(author, keys, 'given-name'),
                'last': key_get(author, keys, 'surname'),
                'initials': key_get(author, keys, 'initials'),
            }
            author_id = self._insert_one('author', author_info)['value']

            paper_author_info = {
                'paper_id': paper_id,
                'author_id': author_id,
                'author_no': int(author['@seq']),
            }
            self._insert_one('paper_author', paper_author_info)

            author_profile_info = {
                'author_id': author_id,
                'address': f'https://www.scopus.com/authid/detail.uri?authorId={author_id_scp}',
                'type': 'Scopus Profile',
            }
            self._insert_one('author_profile', author_profile_info)['value']

            institution_id_scp = key_get(author, keys, 'afid', many=True)
            if institution_id_scp:
                for id_scp in institution_id_scp:
                    if id_scp not in inst_from_author:
                        inst_from_author.append(id_scp)
                    author_institution.append([author_id, institution_id_scp])
        
        inst_ids = {}
        if len(data['affiliation']) < len(inst_from_author):
            result['msg'] = 'mismatch authors and affiliations'
            result['value'] = paper_id
            return result
        for institution in data['affiliation']:
            keys = institution.keys()
            institution_id_scp = int(institution['afid'])
            country_id = None
            if country_data:
                country = key_get(institution, keys, 'affiliation-country')
                if country:
                    country_id = self._read(
                        table_name='country',
                        search={'name': {'value': country_name(country), 'operator': '='}}
                    )['value']
                    if country_id:
                        country_id = country_id[-1][0]
            institution_info = {
                'institution_id_scp': institution_id_scp,
                'name': institution['affilname'],
                'city': key_get(institution, keys, 'affiliation-city'),
                'country_id': country_id,
                'url': f'https://www.scopus.com/affil/profile.uri?afid={institution_id_scp}',
            }
            institution_id = self._insert_one(
                'institution', institution_info)['value']

            department_info = {
                'institution_id': institution_id,
                'name': 'Department Not Available',
                'abbreviation': 'No Dept',
            }
            department_id = self._insert_one(
                'department', department_info)['value']
            inst_ids[institution_id_scp] = [department_id, institution_id]

        for item in author_institution:
            if not item[1]:  # author's "afid" is unknown
                continue
            for id_scp in item[1]:
                author_department_info = {
                    'author_id': item[0],
                    'department_id': inst_ids[id_scp][0],
                    'institution_id': inst_ids[id_scp][1],
                }
                self._insert_one('author_department',
                                    author_department_info)
        # print('raw_insert done')
        result['msg'] = 'Scopus paper inserted'
        result['value'] = paper_id
        return result