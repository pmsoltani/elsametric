import datetime
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from .helpers import get_key, get_row, nullify

from . import (
    Author,
    Author_Profile,
    Country,
    Department,
    Fund,
    Institution,
    Keyword,
    Paper,
    Paper_Author,
    Source,
    Source_Metric,
    Subject
)
from .ext_department_process import ext_department_process


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
