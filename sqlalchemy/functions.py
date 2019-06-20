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
    result = (data[key] if key in keys else None)
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
        result = {'msg': '', 'value': None}
        warnings = data_inspector(data)
        if 'openaccess' in warnings:
            data['openaccess'] = '0'
            warnings.remove('openaccess')
        if 'author:afid' in warnings:
            warnings.remove('author:afid')
        if warnings:
            result['msg'] = warnings
            return result

        keys = data.keys()

        paper_url = ''
        for link in data['link']:
            if link['@ref'] == 'scopus':
                paper_url = link['@href']
                break

        paper_id_scp = int(data['dc:identifier'].split(':')[1])
        query = session.query(Paper) \
            .filter(Paper.id_scp == paper_id_scp) \
            .first()
        if query:
            result['msg'] = 'paper exists'
            result['value'] = query.id
            return result

        source_id_scp = int(data['source-id'])
        agency_id_scp = key_get(data, keys, 'fund-no')
        if agency_id_scp == 'undefined':
            agency_id_scp = None

        source_info = {
            'source_id_scp': source_id_scp,
            'title': data['prism:publicationName'],
            'url': f'https://www.scopus.com/sourceid/{source_id_scp}',
            'type': key_get(data, keys, 'prism:aggregationType'),
            'issn': strip(key_get(data, keys, 'prism:issn'), max_length=8),
            'e_issn': strip(key_get(data, keys, 'prism:eIssn'), max_length=8),
            'isbn': strip(key_get(data, keys, 'prism:isbn'), max_length=13),
            'publisher': None,
            'country_id': None
        }
        source_id = self._insert_one('source', source_info)['value']

        agency_id = None
        if agency_id_scp:
            paper_funding_info = {
                'agency_id_scp': agency_id_scp,
                'agency': key_get(data, keys, 'fund-sponsor'),
                'agency_acronym': key_get(data, keys, 'fund-acr'),
            }
            # print(paper_funding_info)
            agency_id = self._insert_one(
                'paper_funding', paper_funding_info)['value']

        paper_info = {
            'paper_id_scp': paper_id_scp,
            'eid': data['eid'],
            'title': data['dc:title'],
            'type': data['subtype'],
            'type_description': key_get(data, keys, 'subtypeDescription'),
            'abstract': key_get(data, keys, 'dc:description'),
            'total_author': key_get(data, keys, 'author-count'),
            'open_access': data['openaccess'],
            'cited_cnt': data['citedby-count'],
            'url': paper_url,
            'article_no': key_get(data, keys, 'prism:volume'),
            'agency_id': agency_id,
            'retrieval_time': retrieval_time,
            'source_id': source_id,
            'doi': key_get(data, keys, 'prism:doi'),
            'volume': key_get(data, keys, 'prism:volume'),
            'issue': key_get(data, keys, 'prism:issueIdentifier'),
            'page_range': key_get(data, keys, 'prism:pageRange'),
            'date': data['prism:coverDate'],
        }

        if title_length < len(paper_info['title']):
            paper_info['title'] = strip(
                paper_info['title'], max_length=title_length, accepted_chars='')
        paper_id = self._insert_one('paper', paper_info)['value']

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