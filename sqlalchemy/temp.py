import io
import csv

from functions import key_get, strip, country_names, nullify
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
from associations import Paper_Author
from paper import Paper


def paper_process(session, data: dict, retrieval_time: str, keys=None):
    """Imports a paper to database

    Receives a dictionary containing information about a paper and 
    creates a 'Paper' object to be added to the database, if not found.

    Is is assumed that an upstream check has been performed on the input
    data and the availablity of some key nodes in the dictionary (such 
    as paper's Scopus ID) has been confirmed.

    The function performs other checks on the data as well, such as 
    restricting the length of some of the string attributes (including 
    paper title).

    At the end, the Paper object will be examined to check whether it 
    has source, fund, keyword, and author information. If not present, 
    each of these will be added to the Paper object using separate 
    functions.

    Parameters:
        session: a session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information 
            about a paper registered in the Scopus database
        retrieval_time (str): a 'datatime' string pointing to the time
            that the data was retrieved from the Scopus API
        keys: the keys from the data dictionary, to be used by the 
            key_get helper function

    Returns:
        Paper: a 'Paper' object to be added to the database
    """

    if not keys:
        keys = data.keys()

    # there are several links included in the paper's JSON file, we only
    # need a specific one tagged 'scopus'
    paper_url = None
    for link in data['link']:
        if link['@ref'] == 'scopus':
            paper_url = link['@href']
            break

    # an upstream function already confirmed that the paper does have a
    # Scopus ID, otherwise we couldn't go on
    paper_id_scp = int(data['dc:identifier'].split(':')[1])
    paper = session.query(Paper) \
        .filter(Paper.id_scp == paper_id_scp) \
        .first()
    if not paper:  # paper not found in the database
        # There have been cases were the same paper where repeated in
        # the Scopus database twice, with different Scopus IDs. In order
        # to make sure that the paper doesn't exist in our database, we
        # can double check with DOI
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
            ),  # yeah... some paper titles are even longer than 512 chars!
            type=key_get(data, keys, 'subtype'),
            type_description=key_get(data, keys, 'subtypeDescription'),
            abstract=key_get(data, keys, 'dc:description'),
            total_author=key_get(data, keys, 'author-count'),
            open_access=int(key_get(data, keys, 'openaccess')),
            cited_cnt=key_get(data, keys, 'citedby-count'),
            url=paper_url,
            article_no=key_get(data, keys, 'article-number'),
            doi=key_get(data, keys, 'prism:doi'),
            volume=strip(
                key_get(data, keys, 'prism:volume'),
                max_length=45, accepted_chars=''
            ),
            issue=key_get(data, keys, 'prism:issueIdentifier'),
            date=key_get(data, keys, 'prism:coverDate'),
            page_range=key_get(data, keys, 'prism:pageRange'),
            retrieval_time=retrieval_time,
        )

    if not paper.source:
        paper.source = source_process(session, data, keys)

    # FIXME: fund_procees needs re-thinking
    # if not paper.fund:
    #     paper.fund = fund_process(session, data, keys)

    # NOTE: this is an 'all-or-nothing' check, which could cause problems
    if not paper.keywords:
        paper.keywords = keyword_process(session, data, keys)

    # NOTE: this is an 'all-or-nothing' check, which could cause problems
    if not paper.authors:
        authors_list = author_process(session, data, log=False)
        if authors_list:
            for auth in authors_list:
                # using the SQLAlchemy's Association Object
                paper_author = Paper_Author(author_no=auth[0])
                paper_author.author = auth[1]
                paper.authors.append(paper_author)
    
    return paper


def keyword_process(session, data: dict, keys=None, separator: str = '|'):
    """Returns a list of Keyword objects to be added to a Paper object

    Receives a dictionary containing information about a paper and 
    extracts the paper's keywords from it. 

    The function then adds all unique keywords to a list which will be
    added to the upstream Paper object.

    Parameters:
        session: a session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information 
            about a paper registered in the Scopus database
        keys: the keys from the data dictionary, to be used by the 
            key_get helper function
        separator (str): used to split the string from Scopus API which 
            has concatenated the keywords using the '|' character

    Returns:
        list: a list of unique 'Keyword' objects to be added to a 
            'Paper' object
    """
    keywords_list = []
    raw_keywords = key_get(data, keys, 'authkeywords')
    if raw_keywords:
        # Some papers have the same keywords repeated more than once,
        # which can cause problem, since the database has a unique constraint.
        unique_keys_set = set()
        keywords = []
        for key in raw_keywords.split(separator):
            key = key.strip()
            if not key:
                continue

            if key.lower() not in unique_keys_set:
                unique_keys_set.add(key.lower())
                keywords.append(key)

        # at this point, all keywords are stripped and unique within the paper
        for key in keywords:
            keyword = session.query(Keyword) \
                .filter(Keyword.keyword == key) \
                .first()
            if not keyword:  # keyword not in database, let's add it
                keyword = Keyword(keyword=key)
            keywords_list.append(keyword)
    return keywords_list


def source_process(session, data: dict, keys=None):
    """Returns a single Source object to be added to a Paper object 

    Receives a dictionary containing information about a paper and 
    extracts the paper's source from it. 

    Parameters:
        session: a session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information 
            about a paper registered in the Scopus database
        keys: the keys from the data dictionary, to be used by the 
            key_get helper function

    Returns:
        Source: a single 'Source' object to be added to a 'Paper' object
    """
    source = None
    source_id_scp = key_get(data, keys, 'source-id')
    if not source_id_scp:  # data doesn't have Scopus Source ID: can't go on
        return source

    source_id_scp = int(source_id_scp)
    source = session.query(Source) \
        .filter(Source.id_scp == source_id_scp) \
        .first()
    if not source:  # source not in database, let's create one
        title = key_get(data, keys, 'prism:publicationName')
        if not title:  # database has a 'not null' constraint on source title
            title = 'NOT AVAILABLE'

        # strips issn, e_issn, and isbn from any non-alphanumeric chars
        source = Source(
            id_scp=source_id_scp,
            title=title,
            type=key_get(data, keys, 'prism:aggregationType'),
            issn=strip(key_get(data, keys, 'prism:issn'), max_length=8),
            e_issn=strip(key_get(data, keys, 'prism:eIssn'), max_length=8),
            isbn=strip(key_get(data, keys, 'prism:isbn'), max_length=13),
        )
    return source


def fund_process(session, data: dict, keys=None):
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


def author_process(session, data: dict):
    authors_list = []
    author_ids = []
    new_institutions = []
    author_url = 'https://www.scopus.com/authid/detail.uri?authorId='
    if not data['author']:  # data doesn't have any author info: can't go on
        return authors_list
    
    for auth in data['author']:
        keys = auth.keys()
        author_id_scp = key_get(auth, keys, 'authid')
        if not author_id_scp:  # Scopus Author ID not found: go to next author
            continue
        author_id_scp = int(author_id_scp)
        
        # In some cases, the name of an author is repeated more than once
        # in the paper data dictionary. The 'author_ids' variable is used
        # to make a unique list of authors for each paper. Note that this
        # would cause the 'total_author' attribute of the paper to be wrong.

        # TODO: think of a way of correcting the Paper.total_author attribute
        if author_id_scp in author_ids:
            continue
        author_ids.append(author_id_scp)

        author_no = int(auth['@seq'])  # position of author in the paper
        author = session.query(Author) \
            .filter(Author.id_scp == author_id_scp) \
            .first()
        if not author:  # author not in database, let's create one
            author = Author(
                id_scp=author_id_scp,
                first=key_get(auth, keys, 'given-name'),
                last=key_get(auth, keys, 'surname'),
                initials=key_get(auth, keys, 'initials')
            )
            # add the first profile for this author
            author_profile = Author_Profile(
                address=author_url + str(author_id_scp),
                type='Scopus Profile',
            )
            author.profiles.append(author_profile)
        
        # get a list of all institution ids for the author in the paper
        inst_ids = key_get(auth, keys, 'afid', many=True)
        if inst_ids:
            for inst_id in inst_ids:
                # Since all of the institutions mentioned in a paper are
                # added to the database together, we must have a list of
                # to-be-added institutions so that we don't try to add
                # the same institution to the database twice. The variable
                # 'new_institutions' is used to acheive this.
                [institution, department] = institution_process(
                    session, data, inst_id, new_institutions)
                
                if department:
                    author.departments.append(department)
                if institution:  # TODO: is this the best way to check? Test.
                    if institution not in new_institutions:
                        new_institutions.append(institution)
                    
        authors_list.append([author_no, author])
    return authors_list


def institution_process(session, data: dict, inst_id: int, new_institutions: list = [], log: bool = False):
    if log:
        print('Processing institutions and departments')
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
            if log:
                print('INSTITUTION not found in DB')
            institution = next(
                filter(lambda inst: inst.id_scp == inst_id, new_institutions),
                None
            )
            if institution:
                department = session.query(Department) \
                    .with_parent(institution, Institution.departments) \
                    .filter(Department.name == 'Undefined') \
                    .first()
                if log:
                    print(
                        f'INSTITUTION {institution.id_scp} just created but not yet added to DB. Using it again.')
            else:
                institution = Institution(
                    id_scp=institution_id_scp,
                    name=key_get(affil, keys, 'affilname'),
                    city=key_get(affil, keys, 'affiliation-city'),
                )
                country_name = country_names(
                    key_get(affil, keys, 'affiliation-country'))
                if country_name:
                    country = session.query(Country) \
                        .filter(Country.name == country_name) \
                        .first()
                    institution.country = country  # country either found or None

                department = Department(
                    name='Undefined', abbreviation='No Dept.')
                institution.departments.append(department)
                if log:
                    print(
                        f'INSTITUTION not found in DB. Added + Department: {institution.id_scp}')
        else:
            department = session.query(Department) \
                .with_parent(institution, Institution.departments) \
                .filter(Department.name == 'Undefined') \
                .first()
            if log:
                print(
                    f'INSTITUTION already exists: {institution.id_scp}. Department: {department}, {department.name}')
        break
    return [institution, department]


def ext_country_process(session, file_path: str, encoding: str = 'utf-8-sig'):
    """Imports a list of countries to database

    Reads a .csv file and creates 'Country' objects which represent
    rows in the 'country' table in the database. Each country object
    should have the following attributes:
        name: full name of the country
        domain: the 2-character code of the country (ISO 3166-1 alpha-2)
        region: the continent of the country
        sub_region: general geo-graphical location of the country

    It is assumed that each row of the .csv file contains these parts.

    Dependencies(libraries):
        io, csv

    Dependencies(functions):
        nullify: changes any null-looking value to None
        country_names: assigns a unified name to countries with name
            variations

    Parameters:
        session: a session instance of SQLAlchemy session factory to
            interact with the database
        file_path (str): the path to a .csv file containing a list of
            country names with details
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        list: a list of 'Country' objects to be added to the database
    """

    countries_list = []
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            nullify(row)
            country_name = country_names(row['name']).strip()
            country = session.query(Country) \
                .filter(Country.name == country_name) \
                .first()
            if not country:  # country not in database, let's create it
                country = Country(
                    name=country_name, domain=row['domain'].strip(),
                    region=row['region'].strip(),
                    sub_region=row['sub_region'].strip()
                )
                countries_list.append(country)
    return countries_list


def ext_subject_process(session, file_path: str, encoding: str = 'utf-8-sig'):
    """Imports a list of subjects to database

    Reads a .csv file and creates 'Subject' objects which represent
    rows in the 'subject' table in the database. Each Subject object
    has to have the following attributes:
        asjc: All Science Journal Classification Codes - a 4-digit code
            assigned to the subject by Scopus
        top: broad name of the science
        middle: name of the field
        low: name of the field branch

    It is assumed that each row of the .csv file contains these parts.

    Dependencies(libraries):
        io, csv

    Dependencies(functions):
        nullify: changes any null-looking value to None

    Parameters:
        session: a session instance of SQLAlchemy session factory to
            interact with the database
        file_path (str): the path to a .csv file containing a list of
            subjects with details
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        list: a list of 'Subject' objects to be added to the database
    """

    subjects_list = []
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            nullify(row)
            asjc = row['asjc']
            subject = session.query(Subject) \
                .filter(Subject.asjc == asjc) \
                .first()
            if not subject:  # subject not in database, let's create it
                subject = Subject(
                    asjc=asjc,
                    top=row['top'], middle=row['middle'], low=row['low']
                )
                subjects_list.append(subject)
    return subjects_list


def ext_source_process(session, file_path: str, src_type: str = 'Journal',
                       chunk_size: int = 1000, batch_no: int = 0, encoding: str = 'utf-8-sig'):
    """Imports a list of sources to database

    Reads a .csv file and creates 'Source' objects which represent
    rows in the 'source' table in the database. Each Source object
    should have the following attributes:
        id_scp: a unique id assigned to each source by Scopus
        title: title of the source
        type: type of the source (Journal, Conference Proceedings, ...)
        issn: issn of the source
        e_issn: electronic issn of the source
        publisher: source's publisher
        country: country of the source's publisher

    It is assumed that each row of the .csv file contains these parts.

    Dependencies(libraries):
        io, csv

    Dependencies(functions):
        nullify: changes any null-looking value to None

    Parameters:
        session: a session instance of SQLAlchemy session factory to
            interact with the database
        file_path (str): the path to a .csv file containing a list of
            subjects with details
        src_type (str): used to distinguish between files for conference
            proceedings & other source types which are located in 
            separate files
        chunk_size (int): used to break the .csv files into several 
            chunks, since they are very large,
        batch_no (int): the number of the chunk to be processed
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        list: a list of 'Source' objects to be added to the database
    """

    sources_list = []
    batch_max = chunk_size * batch_no
    batch_min = chunk_size * (batch_no - 1)
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for cnt, row in enumerate(reader):
            if batch_no:  # 'cnt' is used to know if a row should be processed
                if (cnt >= batch_max) or (cnt < batch_min):
                    continue

            nullify(row)
            source_id_scp = row['id_scp']
            source = session.query(Source) \
                .filter(Source.id_scp == source_id_scp) \
                .first()
            if not source:  # source not in database, let's create it
                if src_type == 'Journal':
                    source = Source(
                        id_scp=row['id_scp'], title=row['title'],
                        type=row['type'], issn=row['issn'],
                        e_issn=row['e_issn'], publisher=row['publisher'])

                    # 'source' table is related to the 'country' table
                    country_name = country_names(row['country'])
                    if country_name:
                        country = session.query(Country) \
                            .filter(Country.name == country_name) \
                            .first()
                        source.country = country  # country either found or None
                else:
                    source = Source(
                        id_scp=row['id_scp'], title=row['title'],
                        type='Conference Proceedings', issn=row['issn'],
                    )

                if row['asjc']:  # 'source' is related to the 'subject' table
                    for asjc in row['asjc'].split(';'):
                        if not asjc:
                            continue
                        subject = session.query(Subject) \
                            .filter(Subject.asjc == int(asjc)) \
                            .first()
                        if subject:
                            source.subjects.append(subject)

                sources_list.append(source)
    return sources_list


def ext_source_metric_process(session, file_path: str, file_year: int,
                              chunk_size: int = 1000, batch_no: int = 0,
                              encoding: str = 'utf-8-sig', delimiter: str = ';'):
    """Adds source metrics to database

    Reads a .csv file and creates/updates 'Source' objects. The returned
    list of objects will have source metrics data in them, which will be
    added to the 'source_metric' table of the database. Sources already
    in the database will be checked for missing data, such as publisher,
    country, and subjects. If there are metrics available for multiple
    years, the data for each year should be in a separate file and it is
    best to be fed to the function from the most recent year.

    Parameters:
        session: a session instance of SQLAlchemy session factory to
        file_path (str): the path to a .csv file containing a list of
            sources along with metric details
        file_year (int): an integer to indicate the year that the metric
            was evaluated for the source
        chunk_size (int): used to break the .csv files into several 
            chunks, since they are very large,
        batch_no (int): the number of the chunk to be processed
        encoding (str): encoding to be used when reading the .csv file
        delimiter (str): Scimago .csv files use semicolon as delimiter

    Returns:
        list: a list of 'Source' objects which now have metrics, to be 
            added to the database
    """

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
        reader = list(csv.DictReader(csvFile, delimiter=delimiter))
        # 'reader' is converted to list so that we can know its length
        ranked_sources = len(reader)  # used to calculate rank percentiles
        for cnt, row in enumerate(reader):
            if batch_no:  # 'cnt' is used to know if a row should be processed
                if (cnt >= batch_max) or (cnt < batch_min):
                    continue

            keys = row.keys()
            nullify(row)
            source_id_scp = row['Sourceid']
            source = session.query(Source) \
                .filter(Source.id_scp == source_id_scp) \
                .first()
            if not source:  # 'cnt' is used to know if a row should be processed
                source = Source(
                    id_scp=source_id_scp, title=key_get(row, keys, 'Title'),
                    type=key_get(row, keys, 'Type'),
                    issn=None, e_issn=None, isbn=None,
                    publisher=key_get(row, keys, 'Publisher'),
                )

                # some minor modifications to keep the database clean
                if source.type == 'conference and proceedings':
                    source.type = 'Conference Proceedings'
                if source.type:
                    source.type = source.type.title()

            # doing some repairs to sources already in the database, like
            # add missing publisher and country data
            if not source.publisher:
                source.publisher = key_get(row, keys, 'Publisher')

            if not source.country:
                country_name = country_names(row['Country'])
                if country_name:
                    country = session.query(Country) \
                        .filter(Country.name == country_name) \
                        .first()
                    source.country = country  # country either found or None

            if not source.subjects:
                if row['Categories']:
                    # example of row['Categories']
                    # Economics and Econometrics (Q1); Finance (Q1)
                    for low in row['Categories'].split(';'):
                        if not low:
                            continue
                        low = low.strip()
                        if low[-4:] in ['(Q1)', '(Q2)', '(Q3)', '(Q4)']:
                            low = low[:-4].strip()  # removing the '(Qs)'
                        subject = session.query(Subject) \
                            .filter(Subject.low == low) \
                            .first()
                        if subject:
                            source.subjects.append(subject)

            # TODO: This 'if' is too broad. Use query to search whether metrics
            #       are available in the current year
            if not source.metrics:
                total_docs = 0  # used to calculate the CiteScore
                total_cites = 0  # used to calculate the CiteScore
                for item in metric_types[:-1]:
                    if row[item]:
                        if item in ['SJR', 'Cites / Doc. (2years)', 'Ref. / Doc.']:
                            # unfortunately, the decimal points in .csv files by
                            # Scimago are actually commas
                            row[item] = float(row[item].replace(',', '.'))
                        if item == 'SJR Best Quartile':
                            # the database cannot hold values like:
                            # Q1 & Q2, so we must remove the 'Q'
                            row[item] = row[item][-1]

                        source_metric = Source_Metric(
                            type=item, value=row[item], year=file_year)
                        if item == 'Total Docs. (3years)':
                            total_docs = int(row[item])
                        if item == 'Total Cites (3years)':
                            total_cites = int(row[item])
                        if item == f'Total Docs. ({file_year})':
                            source_metric.type = 'Total Docs. (Current Year)'
                        source.metrics.append(source_metric)

                if total_docs and total_cites:  # calculating CiteScore
                    source_metric = Source_Metric(
                        type='CiteScore',
                        value=total_cites / total_docs,
                        year=file_year
                    )
                    source.metrics.append(source_metric)

                # calculating rank percentile
                source_metric = Source_Metric(
                    type='Percentile',
                    value=(int(row['Rank']) - 1) * 100 // ranked_sources + 1,
                    year=file_year
                )
                source.metrics.append(source_metric)

            sources_list.append(source)
    return sources_list


def ext_faculty_process(session, file_path: str, dept_file_path: str,
                        institution_id_scp: int, encoding: str = 'utf-8-sig'):
    """Updates author information with faculty data

    This function uses a .csv file containing faculty data (such as sex,
    department, academic rank, email, ...) of an institution and updates
    authors from the 'author' table in the database that match using
    (Scopus Author ID).

    The function has several parts:
        1. finds the institute in the database using its Scopus ID
        2. finds the 'Undefined' department within the institution that
        was first used to link authors from the institution to it
        3. finds the faculty members of the institution based on their
        Scopus ID
        4. for each faculty:
            a. adds his/her details (sex, department, rank)
            b. adds his/her profiles (email, office phone, website)
            c. adds his/her already created department(s) or create them
            d. unlinks the 'Undefined' department from him/her
        5. adds the updated Author objects to a list and return it

    For each faculty, it is assumed that there are at least 1 Scopus ID
    available. Faculties must also belong to at least 1 department.

    Parameters:
        session: a session instance of SQLAlchemy session factory to
        file_path (str): the path to a .csv file containing a list of
            faculties along with some details
        dept_file_path (str): the path to a .csv file containing a list
            of all department & other 'sub-institutes' belonging to the
            institution
        institution_id_scp (int): the Scopus ID (Affiliation ID) of the
            institution
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        list: a list of 'Author' objects which now have represent 
            faculty members of the institution
    """

    faculties_list = []
    faculty_depts = ext_department_process(dept_file_path, encoding)

    # find the institution in the database
    institution = session.query(Institution) \
        .filter(Institution.id_scp == institution_id_scp) \
        .first()

    if not institution:
        return faculties_list

    # find the 'Undefined' department within the institution
    no_dept = session.query(Department) \
        .with_parent(institution, Institution.departments) \
        .filter(Department.name == 'Undefined') \
        .first()

    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            nullify(row)
            keys = row.keys()
            if not row['Scopus']:  # faculty's Scopus ID not known: can't go on
                continue
            if not row['Departments']:  # faculty's dept. not known: can't go on
                continue

            # some faculties may have more than 1 Scopus ID, but for now,
            # we only use the first one
            faculty_id_scp = int(row['Scopus'].split(',')[0])
            faculty = session.query(Author) \
                .filter(Author.id_scp == faculty_id_scp) \
                .first()
            if not faculty:  # faculty not found in the database: can't to go on
                continue

            # adding faculty details
            sex = key_get(row, keys, 'Sex')
            if sex in ['M', 'F']:
                faculty.sex = sex.lower()
            faculty.type = 'Faculty'
            faculty.rank = key_get(row, keys, 'Rank')

            # adding faculty profiles
            if row['Email']:
                for email in row['Email'].split(','):
                    if not email:
                        continue
                    faculty.profiles.append(
                        Author_Profile(address=email.strip(), type='Email'))
            if row['Office']:
                faculty.profiles.append(
                    Author_Profile(address=row['Office'], type='Phone (Office)'))
            if row['Page']:
                faculty.profiles.append(
                    Author_Profile(address=row['Page'], type='Personal Website'))

            # adding the departments that the faculty belongs to
            for dept in row['Departments'].split(','):
                if not dept:
                    continue
                department = session.query(Department) \
                    .with_parent(institution, Institution.departments) \
                    .filter(Department.abbreviation == dept) \
                    .first()
                if not department:  # department not found, let's create one
                    department = Department(
                        abbreviation=dept,
                        name=faculty_depts[dept]['name'],
                        type=faculty_depts[dept]['type']
                    )
                    institution.departments.append(department)

                faculty.departments.append(department)

            # now that the faculty's departments are known, we can safely
            # unlink the initial 'Undefined' department from that faculty
            # NOTE: Some authors might belong to several institutions at
            # the same time. This means that they might have 'Undefined'
            # departments from their other institutions.
            if no_dept in faculty.departments:
                faculty.departments.remove(no_dept)

            faculties_list.append(faculty)
    return faculties_list


def ext_department_process(file_path: str, encoding='utf-8-sig'):
    """Returns a dictionary of department data

    This function is a helper tool for the function ext_faculty_process.
    It returns a dictionary of department data which will be used to
    assign the departments of each faculty member in the institution.

    Parameters:
        file_path (str): the path to a .csv file containing a list of
            faculties along with some details
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        dict: a dictionary with the following format:
            {dept_abbreviation: {name: dept_full_name, type: dept_type}}
    """

    departments = {}
    with io.open(file_path, 'r', encoding=encoding) as csvFile:
        reader = csv.DictReader(csvFile)
        for row in reader:
            departments[row['Abbreviation']] = {
                'name': row['Full Name'], 'type': row['Type']}
    return departments
