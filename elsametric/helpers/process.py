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

from .author_process import author_process
from .file_process import file_process
from .fund_process import fund_process
from .institution_process import institution_process
from .keyword_process import keyword_process
from .paper_process import paper_process
from .source_process import source_process

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
        country: Optional[Country] = db.query(Country) \
            .filter(Country.name == country_name) \
            .first()
        if not country:  # 'country' not in database, let's create it.
            country = Country(
                name=country_name,
                domain=row['domain'].strip(),
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
        asjc = row['asjc'].strip()
        subject: Optional[Subject] = db.query(Subject) \
            .filter(Subject.asjc == asjc) \
            .first()
        if not subject:  # 'subject' not in database, let's create it.
            subject = Subject(
                asjc=asjc,
                top=row['top'].strip(),
                middle=row['middle'].strip(),
                low=row['low'].strip()
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

    subjects: List[Subject] = db.query(Subject).all()
    # Turn 'subjects' which is a list of 'Subject' objects, into a dict:
    # {asjc1: Subject1, asjc2: Subject2, ...}
    subjects = {subject.asjc: subject for subject in subjects}

    rows = get_row(file_path, encoding)
    for row in rows:
        nullify(row)
        try:
            source_id_scp = int(row['id_scp'])  # possible TypeError
        except TypeError:
            continue
        source: Optional[Source] = db.query(Source) \
            .filter(Source.id_scp == source_id_scp) \
            .first()
        if source:  # 'source' found in database, skipping.
            continue

        # source not in database, let's create it
        if src_type != 'Conference Proceeding':
            source = Source(
                id_scp=source_id_scp, title=row['title'],
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
                id_scp=source_id_scp, title=row['title'],
                type=src_type, issn=row['issn'],
            )

        # adding subject info to the source
        if row['asjc']:
            for asjc in row['asjc'].split(';'):
                try:
                    # possible ValueError, KeyError
                    subject = subjects[int(asjc)]
                    if subject not in source.subjects:
                        # There may be repeated subjects for one source.
                        source.subjects.append(subject)
                except (ValueError, KeyError):
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
