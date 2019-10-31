import io
import csv
import json
import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from .helpers import (
    country_names,
    data_inspector,
    get_key,
    get_row,
    nullify,
    strip
)
from ..models.associations import Paper_Author
from ..models.author import Author
from ..models.author_profile import Author_Profile
from ..models.country import Country
from ..models.department import Department
from ..models.fund import Fund
from ..models.institution import Institution
from ..models.keyword_ import Keyword
from ..models.paper import Paper
from ..models.source import Source
from ..models.source_metric import Source_Metric
from ..models.subject import Subject


def file_process(db: Session, file_path: Path, retrieval_time: str,
                 encoding: str = 'utf8') -> Tuple[dict, list]:
    """Reads a JSON formatted file and creates 'Paper' objects from it

    This function is the upstream of the 'paper_process' function. It
    reads a JSON formatted file located on 'file_path' using 'encoding'
    and then tries to create 'Paper' objects from it using the following
    steps for each entry:
        1. Inspect the entry for possible issues such as lack of 'paper
        title', or Scopus ID. If there are any issues, the 'bad_papers'
        list will be updated with the details of those issues.
        2. Decide if the issues are minor or major. Major ones will stop
        the program from successfully create a Paper object. Some of
        these issues include lack of Scopus ID, 'author', and
        'affiliation' data. Minor issues are the missing data points
        which can be safely replaced with default values; like 'paper
        title' or 'source title', which are replaced with a default
        value later on. Another example is the 'open access' status of
        the paper, which will be defaulted to '0' (closed access).
        3. After ignoring the minor issues, if there are any issues
        left, they would be considered as major and would cause the
        function to seek out the next paper within the file to process.
        If however, there are no remaining issues, the function will
        attempt to call the 'paper_process' function.
        4. After iterating through all entries within the file, the
        function will return a tuple containing a dict of bad_papers
        along with the file_path, and the list of created 'Paper'
        objects. If there is an exception, the function will create a
        report and returns it in a tuple along with an empty list (for
        Paper objects).

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        file_path (Path): the path to a JSON formatted file exported
            from Scopus API containing information about some papers
        retrieval_time (str): a 'datatime' string pointing to the time
            that the data was retrieved from the Scopus API
        encoding (str): encoding to be used when reading the JSON file

    Returns:
        tuple: a tuple containing a dictionary of problems encountered
            when processing the papers and a list of 'Paper' objects
    """

    papers_list = []  # a list of 'Paper' objects to be added to the database
    bad_papers = []  # a list of all papers with issues
    minor_issues = [
        'eid', 'dc:title', 'subtype', 'author-count', 'openaccess',
        'citedby-count', 'source-id', 'prism:publicationName', 'author:afid']

    with io.open(file_path, 'r', encoding=encoding) as raw_file:
        data = json.load(raw_file)

    data = data['search-results']['entry']
    for cnt, entry in enumerate(data):
        issues = data_inspector(entry)
        if issues:
            # Before doing anything, submit the issues to be logged.
            bad_papers.append({'#': cnt, 'issues': [*issues]})

            if 'dc:identifier' in issues:
                # Paper has no Scopus ID, this is a serious problem!
                # The only way around it is to use 'eid' (if available):
                # eid = 2-s2.0-{Scopus ID}
                if 'eid' in issues:  # 'eid' also not found: can't go on
                    continue

                try:
                    # possible AttributeError, ValueError
                    paper_id_scp = int(entry['eid'].replace('2-s2.0-', ''))

                    # Form the 'dc:identifier' key from paper_id_scp
                    entry['dc:identifier'] = f'SCOPUS_ID:{paper_id_scp}'
                    issues.remove('dc:identifier')  # Issue dealt with.
                except (AttributeError, ValueError):
                    # Could not create 'dc:identifier' from 'eid'
                    continue

            bad_papers[-1]['id_scp'] = entry['dc:identifier']

            # Minor issues won't cause any problem for program's flow. Let's
            # filter them out.
            issues = [i for i in issues if i not in minor_issues]
            if issues:  # Any remaining issues are major: can't go on.
                continue

        # At this point, we have no major issues. The program should be able to
        # process the data. If any exceptions occured, we'll catch them below:
        try:
            papers_list.append(paper_process(db, entry, retrieval_time))
        except Exception as e:
            # Since 'paper_process' uses functions of its own, the type of
            # the exception cannot be easily determined.
            try:
                # possible IndexError
                assert bad_papers[-1]['id_scp'] == entry['dc:identifier']
            except (IndexError, AssertionError):  # This is the first bad_paper
                bad_papers.append(
                    {'#': cnt, 'id_scp': entry['dc:identifier']})
            finally:
                bad_papers[-1] = {
                    **bad_papers[-1], 'error_type': type(e), 'error_msg': e}

    problems = {}
    if bad_papers:
        problems = {
            # mask the absolute path
            'file': str(file_path.relative_to(Path.cwd())),
            'papers': bad_papers
        }
    return problems, papers_list


def paper_process(db: Session, data: dict, retrieval_time: str) -> Paper:
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
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information
            about a paper registered in the Scopus database
        retrieval_time (str): a 'datatime' string pointing to the time
            that the data was retrieved from the Scopus API

    Returns:
        Paper: a 'Paper' object to be added to the database
    """

    nullify(data, null_types=(None, '', ' ', '-', '#N/A', 'undefined'))

    # There are several links included in the paper's JSON file, we only
    # need a specific one tagged 'scopus'.
    paper_url = None
    for link in data['link']:
        if link['@ref'] == 'scopus':
            paper_url = link['@href']
            break

    # The upstream function, 'file_process' already confirmed that the paper
    # does have a Scopus ID, otherwise we couldn't go on.
    # Scopus ID format: 'SCOPUS_ID:123456789'. We need what's after colon.
    paper_id_scp = int(data['dc:identifier'].split(':')[1])
    paper_title = strip(
        get_key(data, 'dc:title', default='NOT AVAILABLE'),
        accepted_chars='',
        max_len=512
    )  # Yeah... some paper titles are even longer than 512 chars!
    paper: Optional[Paper] = db.query(Paper) \
        .filter(Paper.id_scp == paper_id_scp) \
        .first()
    if not paper:  # Paper not found in the database.
        # There have been cases were the same paper where repeated in
        # the Scopus database twice, with different Scopus IDs. In order
        # to make sure that the paper doesn't exist in our database, we
        # can double check with DOI:
        paper_doi = get_key(data, 'prism:doi')
        if paper_doi:
            paper = db.query(Paper) \
                .filter(Paper.doi == paper_doi) \
                .first()
            try:
                # There is at least one case that two different papers in the
                # Scopus database had the same DOI (but different Scopus IDs:
                # 84887280754 & 84887287423, as of Oct. 31, 2019), which led
                # the algorithm to come to this point).
                assert paper.title == paper_title
            except AssertionError:  # Different papers with the same DOI
                # Since the current paper is not the same as the one in the
                # database, we need to create it and so we have to set it to
                # None first.
                paper = None
                paper_doi = None
            except AttributeError:  # 'Paper' not found in db. Let's add one.
                pass

    if not paper:  # Paper not in database, let's create one.
        # The 'default' argument for the 'get_key' function is because of the
        # database's 'not null' constraint on certain columns.
        paper = Paper(
            id_scp=paper_id_scp,
            eid=get_key(data, 'eid', default=f'2-s2.0-{paper_id_scp}'),
            title=paper_title,
            type=get_key(data, 'subtype', default='na'),
            type_description=get_key(
                data, 'subtypeDescription', default='NOT AVAILABLE'),
            abstract=get_key(data, 'dc:description'),
            total_author=get_key(data, 'author-count'),
            open_access=int(get_key(data, 'openaccess', default=0)),
            cited_cnt=get_key(data, 'citedby-count'),
            url=paper_url,
            article_no=get_key(data, 'article-number'),
            doi=paper_doi,
            volume=strip(
                get_key(data, 'prism:volume'),
                accepted_chars='',
                max_len=45
            ),
            issue=get_key(data, 'prism:issueIdentifier'),
            date=get_key(data, 'prism:coverDate'),
            page_range=get_key(data, 'prism:pageRange'),
            retrieval_time=retrieval_time,
        )

    # Checking for additional data:
    try:
        assert paper.source
    except (AssertionError, AttributeError):
        paper.source = source_process(db, data)

    try:
        assert paper.fund
    except (AssertionError, AttributeError):
        paper.fund = fund_process(db, data)

    try:
        assert paper.keywords
    except (AssertionError, AttributeError):
        paper.keywords = keyword_process(db, data)

    try:
        assert len(paper.authors) == paper.total_author, 'len'
    except (AssertionError, AttributeError, TypeError) as e:
        try:
            all_authors = [
                paper_author.author for paper_author in paper.authors]
            all_author_id_scps = [author.id_scp for author in all_authors]
        except Exception as e:
            print('@paper_process', type(e), e)
            all_author_id_scps = []

        authors_list = author_process(db, data)
        if len(authors_list) != paper.total_author:
            paper.total_author = len(authors_list)

        for author in authors_list:
            if author[1].id_scp in all_author_id_scps:
                continue
            # Using the SQLAlchemy's Association Object to add paper's authors.
            paper_author = Paper_Author(author_no=author[0])
            paper_author.author = author[1]
            paper.authors.append(paper_author)

    return paper


def keyword_process(db: Session,
                    data: dict, separator: str = '|') -> List[Keyword]:
    """Returns a list of Keyword objects to be added to a Paper object

    Receives a dictionary containing information about a paper and
    extracts the paper's keywords from it.

    The function then adds all unique keywords to a list which will be
    added to the upstream Paper object.

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information
            about a paper registered in the Scopus database
        separator (str): used to split the string from Scopus API which
            has concatenated the keywords using the '|' character

    Returns:
        list: a list of unique 'Keyword' objects to be added to a
            'Paper' object
    """

    keywords_list = []
    raw_keywords: str = get_key(data, 'authkeywords')
    if raw_keywords:
        # Some papers have repeated keywords, which can cause a problem, since
        # the database has a unique constraint on the 'keyword' column.
        unique_keys_set = set()  # just a check variable
        keywords = []
        for raw_keyword in raw_keywords.split(separator):
            try:
                raw_keyword = raw_keyword.strip()
                assert raw_keyword
                assert raw_keyword.lower() not in unique_keys_set
                unique_keys_set.add(raw_keyword.lower())
                keywords.append(raw_keyword)
            except AssertionError:  # Key is repeated in the paper.
                continue

        # At this point, all keywords are stripped and unique within the paper.
        for raw_keyword in keywords:
            keyword: Optional[Keyword] = db.query(Keyword) \
                .filter(Keyword.keyword == raw_keyword) \
                .first()
            try:
                assert keyword
            except AssertionError:  # Keyword not in database, let's add it.
                keyword = Keyword(keyword=raw_keyword)
            finally:
                keywords_list.append(keyword)

    return keywords_list


def source_process(db: Session, data: dict) -> Optional[Source]:
    """Returns a Source object to be added to a Paper object

    Receives a dictionary containing information about a paper and
    extracts the paper's source from it.

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information
            about a paper registered in the Scopus database

    Returns:
        Source: a 'Source' object to be added to a 'Paper' object
    """

    source: Optional[Source] = None
    try:
        source_id_scp = int(get_key(data, 'source-id'))  # possible TypeError
    except TypeError:  # Data doesn't have Scopus Source ID: can't go on.
        return source

    source = db.query(Source) \
        .filter(Source.id_scp == source_id_scp) \
        .first()
    try:
        assert source
    except AssertionError:  # 'source' not in database, let's create one.
        # The 'default' argument for the 'get_key' function is because of the
        # database's 'not null' constraint on certain columns.
        # Strip issn, e_issn, and isbn from any non-alphanumeric chars.
        source = Source(
            id_scp=source_id_scp,
            title=get_key(
                data, 'prism:publicationName', default='NOT AVAILABLE'),
            type=get_key(data, 'prism:aggregationType'),
            issn=strip(get_key(data, 'prism:issn'), max_len=8),
            e_issn=strip(get_key(data, 'prism:eIssn'), max_len=8),
            isbn=strip(get_key(data, 'prism:isbn'), max_len=13),
        )
    return source


def fund_process(db: Session, data: dict) -> Optional[Fund]:
    """Returns a single Source object to be added to a Paper object

    Receives a dictionary containing information about a paper and
    extracts the paper's funding info from it.

    Funding data from the Scopus API has 3 keys:
        fund-no: a code-like string
        fund-sponsor: the name of the funding agency
        fund-acr: the acronym of the funding agency

    Each of these can be absent from the data. An agency can have many
    funds and a fund-no can belong to multiple agencies. This means that
    the database cannot have a unique constrain on any columns, alone.

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information
            about a paper registered in the Scopus database

    Returns:
        Fund: a 'Fund' object to be added to a 'Paper' object
    """

    fund: Optional[Fund] = None

    fund_id_scp = get_key(data, 'fund-no')
    agency = get_key(data, 'fund-sponsor', default='NOT AVAILABLE')
    agency_acronym = get_key(data, 'fund-acr')
    if fund_id_scp == 'undefined':
        fund_id_scp = 'NOT AVAILABLE'
    # DBMSs' Unique Constraints accept rows with one column being null and the
    # other have repeated values. So we must change None to 'NOT AVAILABLE'.

    try:
        assert fund_id_scp != 'NOT AVAILABLE' or agency != 'NOT AVAILABLE'
        fund = db.query(Fund) \
            .filter(Fund.id_scp == fund_id_scp, Fund.agency == agency) \
            .first()
    except AssertionError:
        # Both fund_id_scp & agency are 'NOT AVAILABLE'. Can't go on.
        return fund

    try:
        assert fund
    except AssertionError:  # 'fund' not found in the database, let's add one.
        fund = Fund(
            id_scp=fund_id_scp, agency=agency, agency_acronym=agency_acronym)

    return fund


def author_process(db: Session, data: dict) -> List[list]:
    """Returns a list of Author objects to be added to a Paper object

    Receives a dictionary containing information about a paper and
    extracts the author's info from it, in the form of a list of Author
    objects.

    For each author mentioned in the paper, the function tries to find
    that author in the database. Failing that, it then attempts to
    create an 'Author' object and append the authors Scopus profile to
    that object using a 'Author_Profile' object.

    The function then retrieves a list of Scopus Affiliation IDs for the
    current author and for each affiliation (institution), calls the
    'institution_process' helper function to get the repective
    institution and department objects for that author.

    At the end, the function returns a list of authors, all of them
    having profiles, institutions, and departments.

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information
            about a paper registered in the Scopus database

    Returns:
        list: a list of 'Author' objects to be added to a 'Paper' object
    """

    authors_list = []
    if not data['author']:  # Data doesn't have any author info: can't go on.
        return authors_list

    author_ids = []
    new_institutions = set()
    author_url = 'https://www.scopus.com/authid/detail.uri?authorId='

    for auth in data['author']:
        try:
            author_id_scp = int(get_key(auth, 'authid'))
        except TypeError:  # Scopus Author ID not found: go to next author.
            continue

        # In some cases, the name of an author is repeated more than once
        # in the paper data dictionary. The 'author_ids' variable is used
        # to make a unique list of authors for each paper. Note that this
        # might cause the 'total_author' attribute of the paper to be wrong.

        if author_id_scp in author_ids:
            continue
        author_ids.append(author_id_scp)

        try:
            author_no = int(auth['@seq'])  # Position of author in the paper
        except TypeError:  # The 'author_no' column cannot have null values.
            author_no = 0

        author: Optional[Author] = db.query(Author) \
            .filter(Author.id_scp == author_id_scp) \
            .first()
        if not author:  # 'author' not in database, let's create one.
            author = Author(
                id_scp=author_id_scp,
                first=get_key(auth, 'given-name'),
                last=get_key(auth, 'surname'),
                initials=get_key(auth, 'initials')
            )
            # Add the first profile for this author.
            author_profile = Author_Profile(
                address=author_url + str(author_id_scp),
                type='Scopus Profile',
            )
            author.profiles.append(author_profile)

        # Get a list of all Institution IDs for the author in the paper
        inst_ids = get_key(auth, 'afid', many=True)
        for inst_id in inst_ids:
            # Since all institutions mentioned in a paper are added to the DB
            # together, we must have a list of to-be-added institutions so that
            # we don't try to add the same institution to the database twice.
            # The set 'new_institutions' is used to acheive this.
            institution, department = institution_process(
                db, data, int(inst_id), new_institutions)

            if department:
                author.departments.append(department)
            if institution:
                new_institutions.add(institution)

        authors_list.append([author_no, author])
    return authors_list


def institution_process(
        db: Session, data: dict, inst_id: int,
        new_institutions: set) -> Tuple[
            Optional[Institution], Optional[Department]]:
    """Returns a tuple of (Institution, Department) objects

    Receives a dictionary containing information about a paper and
    extracts the author's affiliation info from it, using the provided
    'inst_id' (Scopus Affiliation ID).

    The function loops through the affiliation data of the paper and if
    it finds a matching Scopus ID, it will try to find the institution
    in (1) the database, (2) the 'new_institutions' set, or (3) create
    it.

    For new institutions, the function creates and appends a Department
    object to it. Since the Scopus API does not provide any information
    regarding the author's department within the institution, the
    function creates a pseudo-department named 'Undefined'.

    Authors' true departments can be reconciled later on, using
    third-party data.

    In the end, the function returns a tuple in the format:
    (Institution, Department) to be added to the current Author object.

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information
            about a paper registered in the Scopus database

    Returns:
        tuple: in the format (Institution, Department) to be added to
            the current Author
    """

    institution = None
    department = None
    if not data['affiliation']:  # No institution info available: can't go on.
        return institution, department

    # From the list of all institutions in a paper, select the one relating to
    # the current author (using Affiliation ID)
    for affil in data['affiliation']:
        try:
            # possible TypeError
            institution_id_scp = int(get_key(affil, 'afid'))
            if inst_id != institution_id_scp:
                raise ValueError
        except (TypeError, ValueError):
            continue

        institution: Optional[Institution] = db.query(Institution) \
            .filter(Institution.id_scp == institution_id_scp) \
            .first()
        if institution:  # 'institution' found in database.
            # It should already have an 'Undefined' department.
            department = db.query(Department) \
                .with_parent(institution, Institution.departments) \
                .filter(Department.name == 'Undefined') \
                .first()
        else:  # 'institution' not in database.
            # Before creating a new institution, search for it in the set of
            # 'new_institutions', which contains institutions that are going
            # to be added to the database (but not added yet).
            institution = next(
                filter(lambda inst: inst.id_scp == inst_id, new_institutions),
                None
            )
            if institution:  # 'institution' found in 'new_institutions' set
                # Institutions in 'new_institutions' set are just created,
                # so they should have only an 'Undefined' department.
                department = institution.departments[0]
            else:  # 'institution' not in 'new_institutions' set: create it.
                # The 'default' argument for the 'get_key' function is
                # because of DB's 'not null' constraint on certain columns.
                institution = Institution(
                    id_scp=institution_id_scp,
                    name=get_key(affil, 'affilname', default='NOT AVAILABLE'),
                    city=get_key(affil, 'affiliation-city'),
                )
                country_name = country_names(
                    get_key(affil, 'affiliation-country'))
                if country_name:
                    country = db.query(Country) \
                        .filter(Country.name == country_name) \
                        .first()
                    institution.country = country  # either found or None
        if not department:
            # Either an institution already in 'new_institutions' set or
            # the database doesn't have an 'Undefined' department, or we are
            # yet to create an 'Undefined' department for a newly created
            # institution (which is more likely the case):
            department = Department(name='Undefined', abbreviation='No Dept.')
            institution.departments.append(department)

        # At this point we have both the institution and the department for
        # current author in the current paper. No need to continue the loop.
        break
    return institution, department


def ext_country_process(
        db: Session, file_path: Path,
        encoding: str = 'utf-8-sig') -> List[Country]:
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
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        file_path (Path): the path to a .csv file containing a list of
            country names with details
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        list: a list of 'Country' objects to be added to the database
    """

    countries_list = []
    rows = get_row(file_path, encoding)
    for row in rows:
        nullify(row)
        country_name = country_names(row['name']).strip()
        country = db.query(Country) \
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


def ext_subject_process(
        db: Session, file_path: Path,
        encoding: str = 'utf-8-sig') -> List[Subject]:
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
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        file_path (Path): the path to a .csv file containing a list of
            subjects with details
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        list: a list of 'Subject' objects to be added to the database
    """

    subjects_list = []
    rows = get_row(file_path, encoding)
    for row in rows:
        nullify(row)
        asjc = row['asjc']
        subject = db.query(Subject) \
            .filter(Subject.asjc == asjc) \
            .first()
        if not subject:  # subject not in database, let's create it
            subject = Subject(
                asjc=asjc,
                top=row['top'], middle=row['middle'], low=row['low']
            )
            subjects_list.append(subject)
    return subjects_list


def ext_source_process(db: Session, file_path: Path, src_type: str = '',
                       encoding: str = 'utf-8-sig') -> List[Source]:
    """Imports a list of sources to database

    Reads a .csv file and creates 'Source' objects which represent
    rows in the 'source' table in the database. Each Source object
    should have the following attributes:
        id_scp: a unique id assigned to each source by Scopus
        title: title of the source
        type: type of the source (Journal, Conference Proceeding, ...)
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
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        file_path (Path): the path to a .csv file containing a list of
            subjects with details
        src_type (str): used to distinguish between files for conference
            proceeding & other source types which are located in
            separate files
        chunk_size (int): used to break the .csv files into several
            chunks, since they are very large,
        batch_no (int): the number of the chunk to be processed
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        list: a list of 'Source' objects to be added to the database
    """

    sources_list = []

    subjects = db.query(Subject).all()
    # Turn 'subjects' which is a list of 'Subject' objects, into a dict:
    # {asjc1: Subject1, asjc2: Subject2, ...}
    subjects = {subject.asjc: subject for subject in subjects}

    rows = get_row(file_path, encoding)
    for row in rows:
        nullify(row)
        source_id_scp = row['id_scp']
        source = db.query(Source) \
            .filter(Source.id_scp == source_id_scp) \
            .first()
        if source:  # source found in database, skipping
            continue

        # source not in database, let's create it
        if src_type != 'Conference Proceeding':
            source = Source(
                id_scp=row['id_scp'], title=row['title'],
                type=row['type'], issn=row['issn'],
                e_issn=row['e_issn'], publisher=row['publisher'])
            # adding country info to the source
            country_name = country_names(row['country'])
            if country_name:
                country = db.query(Country) \
                    .filter(Country.name == country_name) \
                    .first()
                source.country = country  # country either found or None
        else:
            # NOTE: The Scopus data for conference proceedings doesn't
            # include country info.
            source = Source(
                id_scp=row['id_scp'], title=row['title'],
                type=src_type, issn=row['issn'],
            )

        # adding subject info to the source
        if row['asjc']:
            for asjc in row['asjc'].split(';'):
                try:
                    subject = subjects[int(asjc)]
                    if subject not in source.subjects:
                        # there may be repeated subjects for one source
                        source.subjects.append(subject)
                except (ValueError, KeyError):
                    # ValueError: There was a problem converting 'asjc'
                    # to integer; perhaps it was an empty string or
                    # something like ';' or ' '.
                    # KeyError: The asjc code not wasn't found in the
                    # database, which is unusual & unlikely.
                    continue

        sources_list.append(source)
    return sources_list


def ext_source_metric_process(db: Session, file_path: Path, file_year: int,
                              encoding: str = 'utf-8-sig') -> List[Source]:
    sources_list = []

    subjects = db.query(Subject).all()
    # Turn 'subjects' which is a list of 'Subject' objects, into a dict:
    # {asjc1: Subject1, asjc2: Subject2, ...}
    subjects = {subject.asjc: subject for subject in subjects}

    metric_types = {
        'citescore': 'CiteScore', 'percentile': 'Percentile',
        'citations': 'Citations', 'documents': 'Documents',
        'percent_cited': 'Percent Cited', 'snip': 'SNIP', 'sjr': 'SJR'}

    rows = get_row(file_path, encoding)
    for row in rows:
        if not row['id_scp']:
            continue

        nullify(row)
        source_id_scp = row['id_scp']
        source = db.query(Source) \
            .filter(Source.id_scp == source_id_scp) \
            .first()
        if not source:  # source not in database, let's create it
            publisher = get_key(row, 'publisher')
            source = Source(
                id_scp=source_id_scp,
                title=get_key(row, 'title', default='NOT AVAILABLE'),
                type=get_key(row, 'type'),
                issn=strip(get_key(row, 'issn'), max_len=8),
                e_issn=strip(get_key(row, 'e_issn'), max_len=8),
                publisher=publisher
            )

            if publisher:
                # trying to find country using publisher of other sources
                query = db.query(Source) \
                    .filter(
                        Source.publisher == publisher,
                        Source.country != None) \
                    .first()
                if query:
                    source.country = query.country

        if not source.publisher:
            source.publisher = get_key(row, 'publisher')

        if row['asjc']:
            asjc = int(row['asjc'])
            if asjc not in [subj.asjc for subj in source.subjects]:
                try:
                    source.subjects.append(subjects[asjc])
                except KeyError:
                    # The asjc code not wasn't found in the database,
                    # which is unusual & unlikely.
                    # Rolling back the change made to 'source.subjects':
                    if source.subjects == []:
                        source.subjects = None

        # processing metrics
        # creating a dict out of metrics already attached to the source
        source_metrics = {}
        for metric in source.metrics:
            if metric.year == file_year:
                source_metrics[metric.type] = metric

        for metric in metric_types:
            try:
                metric_value = float(row[metric])
            except (KeyError, TypeError, ValueError):  # value not available
                continue
            # using pre-defined names for metrics
            metric = metric_types[metric]
            if metric not in source_metrics:
                source.metrics.append(
                    Source_Metric(
                        type=metric, value=metric_value, year=file_year))
            else:
                if source_metrics[metric].value < metric_value:
                    source_metrics[metric].value = metric_value

        sources_list.append(source)
    return sources_list


def ext_scimago_process(
        db: Session, file_path: Path, file_year: int,
        encoding: str = 'utf-8-sig', delimiter: str = ';') -> List[Source]:
    """Adds source metrics to database

    DEPRECATED FUNCTION: use 'ext_source_metric_process' function.

    Reads a .csv file and creates/updates 'Source' objects. The returned
    list of objects will have source metrics data in them, which will be
    added to the 'source_metric' table of the database. Sources already
    in the database will be checked for missing data, such as publisher,
    country, and subjects. If there are metrics available for multiple
    years, the data for each year should be in a separate file and it is
    best to be fed to the function from the most recent year.

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
        file_path (Path): the path to a .csv file containing a list of
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
    metric_types = [
        'Rank', 'SJR', 'SJR Best Quartile', 'H index',
        f'Total Docs. ({file_year})', 'Total Docs. (3years)', 'Total Refs.',
        'Total Cites (3years)', 'Citable Docs. (3years)',
        'Cites / Doc. (2years)', 'Ref. / Doc.', 'Categories',
    ]
    rows = get_row(file_path, encoding, delimiter)
    for row in rows:
        nullify(row)
        source_id_scp = row['Sourceid']
        source = db.query(Source) \
            .filter(Source.id_scp == source_id_scp) \
            .first()
        if not source:
            source = Source(
                id_scp=source_id_scp,
                title=get_key(row, 'Title', default='NOT AVAILABLE'),
                type=get_key(row, 'Type'),
                issn=None, e_issn=None, isbn=None,
                publisher=get_key(row, 'Publisher'),
            )

            # some minor modifications to keep the database clean
            if source.type == 'conference and proceedings':
                source.type = 'Conference Proceeding'
            if source.type:
                source.type = source.type.title()

        # doing some repairs to sources already in the database, like
        # add missing publisher and country data
        if not source.publisher:
            source.publisher = get_key(row, 'Publisher')

        if not source.country:
            country_name = country_names(row['Country'])
            if country_name:
                country = db.query(Country) \
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
                    subject = db.query(Subject) \
                        .filter(Subject.low == low) \
                        .first()
                    if subject:
                        source.subjects.append(subject)

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

        sources_list.append(source)
    return sources_list


def ext_faculty_process(
        db: Session, file_path: Path, dept_file_path: Path,
        institution_id_scp: int, encoding: str = 'utf-8-sig') -> List[Author]:
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
            a. adds his/her details (preferred name, sex, department,
            rank, google scholar id and metrics)
            b. adds his/her profiles (email, office phone, website)
            c. adds his/her already created department(s) or create them
            d. unlinks the 'Undefined' department from him/her
        5. adds the updated Author objects to a list and return it

    For each faculty, it is assumed that there are at least 1 Scopus ID
    available. Faculties must also belong to at least 1 department.

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
        file_path (Path): the path to a .csv file containing a list of
            faculties along with some details
        dept_file_path (Path): the path to a .csv file containing a list
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
    institution = db.query(Institution) \
        .filter(Institution.id_scp == institution_id_scp) \
        .first()

    if not institution:
        return faculties_list

    # find the 'Undefined' department within the institution
    no_dept = db.query(Department) \
        .with_parent(institution, Institution.departments) \
        .filter(Department.name == 'Undefined') \
        .first()

    rows = get_row(file_path, encoding)
    for row in rows:
        nullify(row)
        if not row['Scopus ID']:  # faculty's Scopus ID not known: can't go on
            continue
        if not row['Departments']:  # faculty's dept. not known: can't go on
            continue

        # some faculties may have more than 1 Scopus ID, but for now,
        # we only use the first one
        faculty_id_scp = int(row['Scopus ID'].split(',')[0])
        faculty = db.query(Author) \
            .filter(Author.id_scp == faculty_id_scp) \
            .first()
        if not faculty:  # faculty not found in the database: can't to go on
            continue

        # adding faculty details
        faculty.id_gsc = get_key(row, 'Google Scholar ID')
        faculty.id_institution = get_key(row, 'Institution ID')
        faculty.first_pref = get_key(row, 'First En') or \
            faculty.first_pref
        faculty.middle_pref = get_key(row, 'Middle En') or \
            faculty.middle_pref
        faculty.last_pref = get_key(row, 'Last En') or faculty.last_pref
        faculty.initials_pref = get_key(row, 'Initials En') or \
            faculty.initials_pref
        faculty.first_fa = get_key(row, 'First Fa')
        faculty.last_fa = get_key(row, 'Last Fa')
        sex = get_key(row, 'Sex')
        if sex in ['M', 'F']:
            faculty.sex = sex.lower()
        faculty.type = 'Faculty'
        faculty.rank = get_key(row, 'Rank')

        retrieval_time_gsc = get_key(
            row, 'Google Scholar Retrieval Time')

        if retrieval_time_gsc:
            # converting int timestamp to datetime
            retrieval_time_gsc = datetime.datetime.fromtimestamp(
                int(retrieval_time_gsc))

            faculty.retrieval_time_gsc = retrieval_time_gsc
            faculty.h_index_gsc = get_key(row, 'Google Scholar h-index')
            faculty.i10_index_gsc = get_key(
                row, 'Google Scholar i10-index')

        # adding faculty profiles
        if row['Email']:
            for email in row['Email'].split(','):
                if not email:
                    continue
                faculty.profiles.append(
                    Author_Profile(address=email.strip(), type='Email'))
        if row['Phone (Office)']:
            faculty.profiles.append(
                Author_Profile(
                    address=row['Phone (Office)'], type='Phone (Office)'))
        if row['Personal Website']:
            faculty.profiles.append(
                Author_Profile(
                    address=row['Personal Website'], type='Personal Website'))
        if row['Google Scholar ID']:
            faculty.profiles.append(
                Author_Profile(
                    address='https://scholar.google.com/citations?user=' +
                    row["Google Scholar ID"],
                    type='Google Scholar'))

        # adding the departments that the faculty belongs to
        for dept in row['Departments'].split(','):
            if not dept:
                continue
            department = db.query(Department) \
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


def ext_department_process(
        file_path: Path, encoding: str = 'utf-8-sig') -> dict:
    """Returns a dictionary of department data

    This function is a helper tool for the function ext_faculty_process.
    It returns a dictionary of department data which will be used to
    assign the departments of each faculty member in the institution.

    Parameters:
        file_path (Path): the path to a .csv file containing a list of
            faculties along with some details
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        dict: a dictionary with the following format:
            {dept_abbreviation: {name: dept_full_name, type: dept_type}}
    """

    departments = {}
    rows = get_row(file_path, encoding)
    for row in rows:
        departments[row['Department Abbreviation']] = {
            'name': row['Department En'], 'type': row['Type']}
    return departments
