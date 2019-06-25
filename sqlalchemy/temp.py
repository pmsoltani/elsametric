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


def keyword_process(session, data, keys=None, separator:str='|'):
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
    for auth in data['author']:
        keys = auth.keys()
        author_id_scp = int(auth['authid'])
        if log:
            print(f'AUTHOR {author_id_scp}')
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
            author.inst_id = key_get(auth, keys, 'afid', many=True)
            if log:
                print(f'AUTHOR not found in DB. Added + Profile. inst_id: {author.inst_id}')
        else:
            inst_ids = key_get(auth, keys, 'afid', many=True)
            author.inst_id = inst_ids
            if log:
                print(f'AUTHOR already exists. inst_id: {author.inst_id}')
        
        if author.inst_id:
            for inst_id in author.inst_id:
                department = institution_process(session, data, inst_id, log=log)
                if log:
                    print(f'Department: {department}')
                author.departments.append(department)
            if log:
                print(f'All AUTHOR departments: {author.departments}')
        if log:
            print()
        authors_list.append([author_no, author])
    return authors_list


def institution_process(session, data, inst_id, log=False):
    if log:
        print('Processing institutions and departments')
    department = None
    for affil in data['affiliation']:
        institution_id_scp = int(affil['afid'])
        if inst_id != institution_id_scp:
            continue
        
        keys = affil.keys()

        institution = session.query(Institution) \
            .filter(Institution.id_scp == institution_id_scp) \
            .first()
        if not institution:
            institution = Institution(
                id_scp=institution_id_scp,
                name=key_get(affil, keys, 'affilname'),
                city=key_get(affil, keys, 'affiliation-city'),
            )
            country_name = key_get(affil, keys, 'affiliation-country')
            country = None
            if country_name:
                country = session.query(Country) \
                    .filter(Country.name == country_name) \
                    .first()
            institution.country = country
            
            department = Department(name='Undefined', abbreviation='No Dept')
            institution.departments.append(department)
            if log:
                print(f'INSTITUTION not found in DB. Added + Department: {institution.id_scp}')
        else:
            departments = institution.departments
            if departments:
                for dept in departments:
                    if dept.name == 'Undefined':
                        department = dept
                        break
            if log:
                print(f'INSTITUTION already exists. {institution.id_scp}')
        break
    return department


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
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for cnt, row in enumerate(reader):
            if batch_no:
                if (cnt >= (chunk_size * batch_no)) or (cnt < (chunk_size * (batch_no - 1))):
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
                        id_scp=row['id_scp'], title=row['title'], type=row['type'],
                        issn=row['issn'], e_issn=row['e_issn'], publisher=row['publisher']
                    )
                    country_name = country_names(row['country'])
                    if country_name:
                        country = session.query(Country) \
                            .filter(Country.name == country_name) \
                            .first()
                        source.country = country
                else:
                    source = Source(
                        id_scp=row['id_scp'], title=row['title'], type='Conference Proceedings',
                        issn=row['issn'],
                    )
                
                if row['asjc']:
                    subject_codes = [int(code) 
                                    for code in row['asjc'].split(';') if code != '']
                    for asjc in subject_codes:
                        subject = session.query(Subject) \
                            .filter(Subject.asjc == asjc) \
                            .first()
                        if subject:
                            source.subjects.append(subject)
                
                sources_list.append(source)
    return sources_list


def ext_source_metric_process(session, file_path, file_year, 
    encoding='utf-8-sig'):
    sources_list = []
    metric_types = [
        'Rank', 'SJR', 'SJR Best Quartile', 'H index', 
        f'Total Docs. ({file_year})', 'Total Docs. (3years)', 'Total Refs.', 
        'Total Cites (3years)', 'Citable Docs. (3years)', 
        'Cites / Doc. (2years)', 'Ref. / Doc.', 'Categories'
    ]
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            for key in row:
                if (not row[key]) or (row[key] == '-'):
                    row[key] = None
            source_id_scp = row['Sourceid']
            source = session.query(Source) \
                .filter(Source.id_scp == source_id_scp) \
                .first()
            if not source:
                keys = row.keys()
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
            
            if not source.publisher:
                source.publisher = key_get(row, keys, 'Publisher')
            
            if not source.country:
                country_name = country_names(row['country'])
                if country_name:
                    country = session.query(Country) \
                        .filter(Country.name == country_name) \
                        .first()
                    source.country = country
            
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

            for item in metric_types:
                if row[item]:
                    source_metric = Source_Metric(
                        type=item,
                        value=row[item],
                        year=file_year
                    )
                    source.metrics.append(source_metric)
            # source_metric = Source_Metric(
            #     type=
            # )

# - it's best to return a list of sources, each of them having several metrics
# - after inserting the metrics present in the csv file, calculate others such
#   as CiteScore, or ImpactFactor (if possible)
# - think about a way to add Q1-Q4 metrics to each 'low' subject of each source
# - since the csv files contain everything needed to instantiate a new source:
#   * add sources if not found
#   * repair sources if needed (publisher, country, and other data)
#   - since some the source info might change over the years (like publisher)
#     it would be best to start from 2018 and move backwards
# - use the 'Rank' column to add a 'Percentile' metric to each journal, but
#   first do some research about the definitions of quartiles and percentiles


    return subjects_list