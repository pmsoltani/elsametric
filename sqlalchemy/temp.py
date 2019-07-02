import io
import csv
from collections import OrderedDict

from functions import key_get, strip, country_names
from keyword_ import Keyword
from source import Source
from source_metric import Source_Metric
from fund import Fund
from author import Author
from author_profile import Author_Profile
from institution import Institution
from department import Department
from country import Country
from subject import Subject
from paper import Paper


def paper_process(session, data, retrieval_time, keys=None):
    if not keys:
        keys = data.keys()

    paper_url = ''
    for link in data['link']:
        if link['@ref'] == 'scopus':
            paper_url = link['@href']
            break

    paper_id_scp = int(data['dc:identifier'].split(':')[1])
    paper = session.query(Paper) \
        .filter(Paper.id_scp == paper_id_scp) \
        .first()
    if not paper:
        # double check with DOI
        doi = key_get(data, keys, 'prism:doi')
        if doi:
            paper = session.query(Paper) \
                .filter(Paper.doi == doi) \
                .first()
        if not paper:
            paper = Paper(
                id_scp=paper_id_scp,
                eid=key_get(data, keys, 'eid'),
                title=strip(
                    key_get(data, keys, 'dc:title'),
                    max_length=512, accepted_chars=''
                ),
                type=key_get(data, keys, 'subtype'),
                type_description=key_get(data, keys, 'subtypeDescription'),
                abstract=key_get(data, keys, 'dc:description'),
                total_author=key_get(data, keys, 'author-count'),
                open_access=int(key_get(data, keys, 'openaccess')),
                cited_cnt=key_get(data, keys, 'citedby-count'),
                url=paper_url,
                article_no=key_get(data, keys, 'article-number'),
                doi=key_get(data, keys, 'prism:doi'),
                volume=key_get(data, keys, 'prism:volume'),
                issue=key_get(data, keys, 'prism:issueIdentifier'),
                date=key_get(data, keys, 'prism:coverDate'),
                page_range=key_get(data, keys, 'prism:pageRange'),
                retrieval_time=retrieval_time,
            )
    return paper


def keyword_process(session, data, keys=None, separator: str = '|'):
    keywords_list = []
    author_keywords = key_get(data, keys, 'authkeywords')
    if author_keywords:
        terms_list = [key.strip() for key in author_keywords.split(separator)]
        # making sure unique keywords... case insensitive
        seen, result = set(), []
        for item in terms_list:
            if item.lower() not in seen:
                seen.add(item.lower())
                result.append(item)
        terms = result

        for term in terms:
            keyword = session.query(Keyword) \
                .filter(Keyword.keyword == term) \
                .first()
            if not keyword:
                keyword = Keyword(
                    keyword=term
                )
            keywords_list.append(keyword)
    return keywords_list


def source_process(session, data, keys=None):
    if not keys:
        keys = data.keys()

    source_id_scp = int(data['source-id'])
    source = session.query(Source) \
        .filter(Source.id_scp == source_id_scp) \
        .first()
    if not source:
        source = Source(
            id_scp=source_id_scp,
            title=key_get(data, keys, 'prism:publicationName'),
            type=key_get(data, keys, 'prism:aggregationType'),
            issn=strip(key_get(data, keys, 'prism:issn'), max_length=8),
            e_issn=strip(key_get(data, keys, 'prism:eIssn'), max_length=8),
            isbn=strip(key_get(data, keys, 'prism:isbn'), max_length=13),
        )
    return source


def fund_process(session, data, keys=None):
    if not keys:
        keys = data.keys()

    fund_id_scp = key_get(data, keys, 'fund-no')
    if fund_id_scp == 'undefined':
        fund_id_scp = None
    agency = key_get(data, keys, 'fund-sponsor')
    agency_acronym = key_get(data, keys, 'fund-acr')

    fund = None
    if fund_id_scp or agency:
        fund = session.query(Fund) \
            .filter(Fund.id_scp == fund_id_scp, Fund.agency == agency) \
            .first()
        if not fund:
            fund = Fund(
                id_scp=fund_id_scp,
                agency=agency, agency_acronym=agency_acronym
            )
    return fund


def author_process(session, data, log=False):
    authors_list = []
    new_institutions = []
    for auth in data['author']:
        keys = auth.keys()
        author_id_scp = int(auth['authid'])
        if log: print(f'AUTHOR {author_id_scp}')
        author_no = int(auth['@seq'])
        author = session.query(Author) \
            .filter(Author.id_scp == author_id_scp) \
            .first()
        if not author:
            author = Author(
                id_scp=author_id_scp,
                first=key_get(auth, keys, 'given-name'),
                last=key_get(auth, keys, 'surname'),
                initials=key_get(auth, keys, 'initials')
            )
            author_profile = Author_Profile(
                address=f'https://www.scopus.com/authid/detail.uri?authorId={author_id_scp}',
                type='Scopus Profile',
            )
            author.profiles.append(author_profile)
            inst_ids = key_get(auth, keys, 'afid', many=True)
            if log: print(f'AUTHOR not found in DB. Added + Profile. inst_id: {inst_ids}')
        else:
            inst_ids = key_get(auth, keys, 'afid', many=True)
            if log: print(f'AUTHOR already exists. inst_id: {inst_ids}')

        if inst_ids:
            for inst_id in inst_ids:
                [institution, department] = institution_process(
                    session, data, inst_id, new_institutions, log=log)
                if department:
                    author.departments.append(department)
                
                if institution:
                    if not new_institutions:
                        new_institutions.append(institution)
                    else:
                        if institution.id_scp not in [inst.id_scp for inst in new_institutions]:
                            new_institutions.append(institution)
                
                if log: print(f'Department: {department}')
            if log: print(f'All AUTHOR departments: {author.departments}')
        if log: print()
        authors_list.append([author_no, author])
    return authors_list


def institution_process(session, data, inst_id, new_institutions=[], log=False):
    if log: print('Processing institutions and departments')
    department = None
    institution = None
    for affil in data['affiliation']:
        institution_id_scp = int(affil['afid'])
        if inst_id != institution_id_scp:
            continue

        keys = affil.keys()

        institution = session.query(Institution) \
            .filter(Institution.id_scp == institution_id_scp) \
            .first()
        if not institution:
            if log: print('INSTITUTION not found in DB')
            institution = list(filter(lambda inst: inst.id_scp == inst_id, new_institutions))
            if institution:
                institution = institution[0]
                department = list(filter(lambda dept: dept.name == 'Undefined', institution.departments))[0]
                if log: print(f'INSTITUTION {institution.id_scp} just created but not yet added to DB. Using it again.')
            else:
                institution = Institution(
                    id_scp=institution_id_scp,
                    name=key_get(affil, keys, 'affilname'),
                    city=key_get(affil, keys, 'affiliation-city'),
                )        
                country_name = country_names(key_get(affil, keys, 'affiliation-country'))
                country = None
                if country_name:
                    country = session.query(Country) \
                        .filter(Country.name == country_name) \
                        .first()
                institution.country = country
                
                department = Department(name='Undefined', abbreviation='No Dept.')
                institution.departments.append(department)
                if log: print(f'INSTITUTION not found in DB. Added + Department: {institution.id_scp}')
        else:
            if institution.departments:
                department = list(filter(lambda dept: dept.name == 'Undefined', institution.departments))[0]
            if log: print(f'INSTITUTION already exists: {institution.id_scp}. Department: {department}, {department.name}')
        break
    return [institution, department]


def ext_country_process(session, file_path, encoding='utf-8-sig'):
    countries_list = []
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            for key in row:
                if not row[key]:
                    row[key] = None
            country_name = country_names(row['name'])
            country = session.query(Country) \
                .filter(Country.name == country_name) \
                .first()
            if not country:
                country = Country(
                    name=country_name, domain=row['domain'],
                    region=row['region'], sub_region=row['sub_region']
                )
                countries_list.append(country)
    return countries_list


def ext_subject_process(session, file_path, encoding='utf-8-sig'):
    subjects_list = []
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            for key in row:
                if not row[key]:
                    row[key] = None
            asjc = row['asjc']
            subject = session.query(Subject) \
                .filter(Subject.asjc == asjc) \
                .first()
            if not subject:
                subject = Subject(
                    asjc=asjc,
                    top=row['top'], middle=row['middle'], low=row['low']
                )
                subjects_list.append(subject)
    return subjects_list


def ext_source_process(session, file_path, src_type='Journal',
                       chunk_size=1000, batch_no=0, encoding='utf-8-sig'):
    sources_list = []
    batch_max = chunk_size * batch_no
    batch_min = chunk_size * (batch_no - 1)
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for cnt, row in enumerate(reader):
            if batch_no:
                if (cnt >= batch_max) or (cnt < batch_min):
                    continue
            for item in row:
                if not row[item]:
                    row[item] = None
            source_id_scp = row['id_scp']
            source = session.query(Source) \
                .filter(Source.id_scp == source_id_scp) \
                .first()
            if not source:
                if src_type == 'Journal':
                    source = Source(
                        id_scp=row['id_scp'], title=row['title'],
                        type=row['type'], issn=row['issn'],
                        e_issn=row['e_issn'], publisher=row['publisher']
                    )
                    country_name = country_names(row['country'])
                    if country_name:
                        country = session.query(Country) \
                            .filter(Country.name == country_name) \
                            .first()
                        source.country = country
                else:
                    source = Source(
                        id_scp=row['id_scp'], title=row['title'],
                        type='Conference Proceedings', issn=row['issn'],
                    )

                if row['asjc']:
                    subject_codes = [
                        int(code) for code in row['asjc'].split(';') if code != '']
                    for asjc in subject_codes:
                        subject = session.query(Subject) \
                            .filter(Subject.asjc == asjc) \
                            .first()
                        if subject:
                            source.subjects.append(subject)

                sources_list.append(source)
    return sources_list


def ext_source_metric_process(session, file_path, file_year,
                              chunk_size=1000, batch_no=0, encoding='utf-8-sig', 
                              delimiter=';', log=False):
    sources_list = []
    batch_max = chunk_size * batch_no
    batch_min = chunk_size * (batch_no - 1)
    metric_types = [
        'Rank', 'SJR', 'SJR Best Quartile', 'H index',
        f'Total Docs. ({file_year})', 'Total Docs. (3years)', 'Total Refs.',
        'Total Cites (3years)', 'Citable Docs. (3years)',
        'Cites / Doc. (2years)', 'Ref. / Doc.', 'Categories',
    ]
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        if log: print('@ with')
        reader = csv.DictReader(csvFile, delimiter=delimiter)
        reader = list(reader)
        ranked_sources = len(reader)
        if log: print('len:', ranked_sources)
        for cnt, row in enumerate(reader):
            if log: print('@ reader', cnt)
            if batch_no:
                if log: print('@ batch')
                if (cnt >= batch_max) or (cnt < batch_min):
                    continue
            keys = row.keys()
            for key in row:
                if (not row[key]) or (row[key] == '-'):
                    row[key] = None
            source_id_scp = row['Sourceid']
            source = session.query(Source) \
                .filter(Source.id_scp == source_id_scp) \
                .first()
            if not source:
                if log: print('@ not source: creating')
                source = Source(
                    id_scp=source_id_scp, title=key_get(row, keys, 'Title'),
                    type=key_get(row, keys, 'Type'),
                    issn=None, e_issn=None, isbn=None,
                    publisher=key_get(row, keys, 'Publisher'),
                )
                if source.type == 'conference and proceedings':
                    source.type = 'Conference Proceedings'
                if source.type:
                    source.type = source.type.title()
                if log: print(source.type)

            if not source.publisher:
                source.publisher = key_get(row, keys, 'Publisher')
                if log: print(
                        f'new publisher for {source.id_scp}: {source.publisher}')

            if not source.country:
                country_name = country_names(row['Country'])
                if country_name:
                    country = session.query(Country) \
                        .filter(Country.name == country_name) \
                        .first()
                    source.country = country
                    if log: print(
                            f'new country for {source.id_scp}: {source.country}')

            if not source.subjects:
                if row['Categories']:
                    subject_low = [low.strip() for low in
                                   row['Categories'].split(';') if low != '']
                    for low in subject_low:
                        if low[-4:] in ['(Q1)', '(Q2)', '(Q3)', '(Q4)']:
                            low = low[:-4].strip()

                        subject = session.query(Subject) \
                            .filter(Subject.low == low) \
                            .first()
                        if subject:
                            source.subjects.append(subject)
                    if log: print(f'new subjects for {source.id_scp}:', [
                              sub.asjc for sub in source.subjects])

            if not source.metrics:
                total_docs = 0
                total_cites = 0
                for item in metric_types[:-1]:
                    if log: print('@ metrics')
                    if row[item]:
                        if item in ['SJR', 'Cites / Doc. (2years)', 'Ref. / Doc.']:
                            row[item] = float(row[item].replace(',', '.'))
                        if item == 'SJR Best Quartile':
                            row[item] = row[item][-1]

                        source_metric = Source_Metric(
                            type=item,
                            value=row[item],
                            year=file_year
                        )
                        if item == 'Total Docs. (3years)':
                            total_docs = int(row[item])
                        if item == 'Total Cites (3years)':
                            total_cites = int(row[item])
                        if item == f'Total Docs. ({file_year})':
                            source_metric.type = 'Total Docs. (Current)'
                        source.metrics.append(source_metric)

                if total_docs and total_cites:
                    if log: print('@ citescore')
                    source_metric = Source_Metric(
                        type='CiteScore',
                        value=total_cites / total_docs,
                        year=file_year
                    )
                    source.metrics.append(source_metric)

                source_metric = Source_Metric(
                    type='Percentile',
                    value=((int(row['Rank']) - 1) * 100 // ranked_sources) + 1,
                    year=file_year
                )
                if log: print('@ percentile')
                source.metrics.append(source_metric)

                if log:
                    for met in source.metrics:
                        print(met.type, met.value)
            sources_list.append(source)

    return sources_list
