import mysql.connector as mysql


def data_inspector(data: dict):
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


def key_get(data: dict, keys, key: str, many: bool = False):
    result = (data[key] if key in keys else None)
    if type(result) == list:
        if not many:
            return result[0]['$']
        return [int(item['$']) for item in result]
    if type(result) == dict:
        return result['$']
    return result


def strip(data, max_length: int = 8, accepted_chars: str = '0123456789xX', force_strip: bool = True):
    if not data:
        return data
    if not accepted_chars:
        return data.strip()[:max_length]
    if force_strip:
        return ''.join([char for char in data if char in accepted_chars])[:max_length]
    return ''.join([char for char in data if char in accepted_chars])


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


class Database:

    table_ids = {
        'source': {'order': 0, 'id': ['source_id_scp']},
        'subject': {'order': 0, 'id': ['asjc_code']},
        'country': {'order': 0, 'id': ['name']},
        'paper_funding': {'order': 0, 'id': ['agency_id_scp']},

        'source_subject': {'order': 1, 'id': ['source_id', 'subject_id']},
        'paper': {'order': 1, 'id': ['paper_id_scp']},

        'author': {'order': 2, 'id': ['author_id_scp']},
        'keyword': {'order': 2, 'id': ['keyword_id']},

        'paper_author': {'order': 3, 'id': ['paper_id', 'author_id']},
        'paper_keyword': {'order': 3, 'id': ['paper_id', 'keyword_id']},
        'author_profile': {'order': 3, 'id': ['author_id']},
        'institution': {'order': 3, 'id': ['institution_id_scp']},

        'department': {'order': 4, 'id': ['institution_id', 'name']},

        'author_department': {'order': 5, 'id': ['author_id', 'department_id', 'institution_id']},
    }

    def __init__(self, config: dict, db_name: str,
                 host: str = 'localhost', port: int = 3306, buffered: bool = True):
        self._params = {
            'host': host,
            'buffered': buffered,
            'user': config['MySQL User'],
            'pass': config['MySQL Pass'],
        }
        self.db_name = db_name
        self.db = None
        self.cursor = None
        self.tables = []

    def _connect(self):
        if not self.db:
            self.db = mysql.connect(
                host=self._params['host'],
                buffered=self._params['buffered'],
                user=self._params['user'],
                password=self._params['pass'],
                database=self.db_name
            )
        return self.db

    def _cursor(self):
        if not self.db:
            self._connect()
        if not self.db.is_connected():
            self.db.reconnect()
        if not self.cursor:
            self.cursor = self.db.cursor()
        return self.cursor

    def _execute(self, query, values=[], fetch: bool = False,
                 many: bool = False, close_cursor: bool = False):
        if many:
            self._cursor().executemany(query, values)
        else:
            self._cursor().execute(query, values)
        if fetch:
            server_response = self.cursor.fetchall()
        else:
            server_response = self.cursor
        if close_cursor:
            self.cursor.close()
            self.cursor = None
        return server_response

    def _close(self):
        if self.db.is_connected():
            self.db.close()

    def _show_tables(self):
        return [table[0] for table in self._execute(query='SHOW TABLES', fetch=True)]

    def _has_table(self, table_name):
        table_names = self._show_tables()
        if table_name in table_names:
            return True
        return False

    def _column_names(self, table_name):
        return [col[0] for col in self.describe(table_name)]

    def describe(self, table_name: str = ''):
        if table_name:
            query = f'DESCRIBE {table_name}'
            return self._execute(query=query, fetch=True)
        server_response = self._show_tables()
        for table in server_response:
            self.tables.append({table: self.describe(table)})
        return self.tables

    def _read(self, table_name: str, search: dict, select: str = '*', result_columns: bool = False):
        result = {'msg': '', 'value': None}
        # print('@ _read')
        # if not self._has_table(table_name):
        #     result['msg'] = f'Error! "{table_name}" table not found'
        #     return result

        values = []
        if search:
            query_list = []
            query = f'SELECT {select} FROM {table_name} WHERE '
            for k, v in search.items():
                query_list.append(f'{k} {v["operator"]} %s')
                values.append(v['value'])
            query += " AND ".join(query_list)
            values = tuple(value for value in values)
        else:
            query = f'SELECT {select} FROM {table_name}'
            values = tuple()
        # print(f'query: {query}')
        server_response = self._execute(
            query=query, values=values, fetch=True, close_cursor=True)
        result['msg'] = 'Read query successful.'
        if result_columns:
            result['value'] = []
            if select == '*':
                data_columns = self._column_names(table_name)
            else:
                data_columns = [column.strip() for column in select.split(',')]
            for row in server_response:
                result['value'].append(
                    {column: value for column, value in zip(data_columns, row)})
            # print('_read done!')
            return result
        # print('_read done!')
        result['value'] = server_response
        return result

    def _insert_one(self, table_name, data: dict):
        result = {'msg': '', 'value': None}
        # if not self._has_table(table_name):
        #     result['msg'] = f'Error! "{table_name}" table not found'
        #     return result

        # table_columns = self._column_names(table_name)
        data_columns = list(data.keys())
        # for col in data_columns:
        #     if col not in table_columns:
        #         result['msg'] = f'Error! "{col}" column not found'
        #         return result

        # check if the record already exists
        id_columns = Database.table_ids[table_name]['id']
        # print(f'id_columns: {id_columns}')
        search = {id_column: {
            'value': data[id_column], 'operator': '='} for id_column in id_columns}
        # print(f'search: {search}')
        server_response = self._read(table_name, search)['value']
        if server_response:  # record exists, let's return the its primary key
            server_response = server_response[-1][0]
            result['msg'] = f'Table "{table_name}" already has this record'
            result['value'] = server_response
            return result

        # record is new
        query = f'INSERT INTO {table_name} ({", ".join(data_columns)}) VALUES ({"%s, " * (len(data_columns) - 1)}%s)'
        values = tuple(data[col] for col in data_columns)
        try:
            self._execute(query, values)
            # print('_insert_one done!')
            self.db.commit()
            server_response = self.cursor.lastrowid
            self._close()
            result['msg'] = f'Record added to "{table_name}"'
            result['value'] = server_response
            return result
        except Exception as e:
            self._close()
            result['msg'] = f'Error on _insert_one: {e}'
            return result

    def _insert_many(self, table_name, data: list):
        # data is a list of dictionaries
        # print('@ _insert_many')
        result = {'msg': '', 'value': None}
        if not self._has_table(table_name):
            result['msg'] = f'Error! "{table_name}" table not found'
            return result

        # assuming all data rows have the same columns
        # data is a list of dictionaries, of which the keys are column names
        table_columns = self._column_names(table_name)
        data_columns = list(data[0].keys())
        for col in data_columns:
            if col not in table_columns:
                result['msg'] = f'Error! "{col}" column not found'
                return result

        query = f'INSERT INTO {table_name} ({", ".join(data_columns)}) VALUES ({"%s, " * (len(data_columns) - 1)}%s)'
        values = []

        id_columns = Database.table_ids[table_name]['id']
        skipped_rows = 0
        total_rows = len(data)
        for row in data:
            search = {id_column: {
                'value': row[id_column], 'operator': '='} for id_column in id_columns}
            if self._read(table_name, search)['value']:
                skipped_rows += 1
                continue
            values.append(tuple(row[col] for col in data_columns))
        try:
            self._execute(query, values, many=True)
            # print('_insert done!')
            self.db.commit()
            server_response = self.cursor.lastrowid
            self._close()
            result['msg'] = f'{total_rows - skipped_rows} records added ({skipped_rows} already existed)'
            result['value'] = server_response
            return result
        except Exception as e:
            self._close()
            result['msg'] = f'Error on _insert_many: {e}'
            return result

    def _update_one(self, table_name, data: dict, null_scape: bool = False):
        result = {'msg': '', 'value': None}
        # if not self._has_table(table_name):
        #     result['msg'] = f'Error! "{table_name}" table not found'
        #     return result

        # table_columns = self._column_names(table_name)
        # for col in data:
        #     if col not in table_columns:
        #         result['msg'] = f'Error! "{col}" column not found'
        #         return result

        id_columns = Database.table_ids[table_name]['id']

        query = f'UPDATE {table_name} SET '
        set_list = []
        where_list = []
        values = {'set': [], 'where': []}
        search = {}
        for k, v in data.items():
            if k not in id_columns:
                if (null_scape) and (not v):
                    continue
                set_list.append(f'`{k}` = %s')
                values['set'].append(v)
            else:
                where_list.append(f'`{k}` = %s')
                values['where'].append(v)
                search[k] = {'value': v, 'operator': '='}
        query += ', '.join(set_list) + ' WHERE ' + ' AND '.join(where_list)
        values = tuple(value for value in values['set'] + values['where'])
        try:
            self._execute(query, values)
            # print('_insert_one done!')
            self.db.commit()
            server_response = self._read(
                table_name=table_name,
                search=search
            )['value']
            if server_response:
                server_response = server_response[-1][0]
            self._close()
            result['msg'] = f'Record of "{table_name}" updated'
            result['value'] = server_response
            return result
        except Exception as e:
            self._close()
            result['msg'] = f'error on _update_one: {e}'
            return result
    
    def raw_insert(self, data: list, retrieval_time, title_length: int = 300, country_data: bool = False):
        # print('@ raw_insert')
        # data is a dictionary containing the info about 1 paper
        result = {'msg': '', 'value': None}
        warnings = data_inspector(data)
        if 'openaccess' in warnings:
            data['openaccess'] = '0'
            warnings.remove('openaccess')
        if 'author:afid' in warnings:
            warnings.remove('author:afid')
        if len(warnings):
            self._close()
            result['msg'] = warnings
            return result

        keys = data.keys()

        paper_url = ''
        for link in data['link']:
            if link['@ref'] == 'scopus':
                paper_url = link['@href']
                break

        paper_id_scp = int(data['dc:identifier'].split(':')[1])
        server_response = self._read(
            table_name='paper',
            search={'paper_id_scp': {'value': paper_id_scp, 'operator': '='}}
        )['value']
        if server_response:
            self._close()
            result['msg'] = 'paper exists'
            result['value'] = server_response[-1][0]
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