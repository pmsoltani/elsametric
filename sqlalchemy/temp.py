from functions import key_get, strip
from keyword_ import Keyword
from source import Source
from fund import Fund
from author import Author
from author_profile import Author_Profile
from institution import Institution
from department import Department
from country import Country

def keyword_process(session, author_keywords, separator:str='|'):
    keywords_list = []
    if author_keywords:
        terms = [key.strip() for key in author_keywords.split(separator)]
        
        for term in terms:
            keyword = session.query(Keyword) \
                .filter(Keyword.keyword == term) \
                .first()
            if not keyword:
                # new keyword
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


def author_process(session, data):
    authors_list = []
    for auth in data['author']:
        keys = auth.keys()
        author_id_scp = int(auth['authid'])
        print(f'AUTHOR {author_id_scp}')
        # paper_author = Paper_Author(int(auth['@seq']))
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
            print(f'AUTHOR not found in DB. Added + Profile. inst_id: {author.inst_id}')
        else:
            inst_ids = key_get(auth, keys, 'afid', many=True)
            author.inst_id = inst_ids
            print(f'AUTHOR already exists. inst_id: {author.inst_id}')
        
        for inst_id in author.inst_id:
            department = institution_process(session, data, inst_id)
            print(f'Department: {department}')
            author.departments.append(department)
        print(f'All AUTHOR departments: {author.departments}')
        print()
        authors_list.append(author)
    return authors_list

def institution_process(session, data, inst_id):
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
            print(f'INSTITUTION not found in DB. Added + Department: {institution.id_scp}')
        else:
            departments = institution.departments
            if departments:
                for dept in departments:
                    if dept.name == 'Undefined':
                        department = dept
                        break
            print(f'INSTITUTION already exists. {institution.id_scp}')
        break
    return department