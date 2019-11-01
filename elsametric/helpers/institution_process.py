from typing import Optional, Tuple

from sqlalchemy.orm import Session

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

from .helpers import country_names, get_key


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
            department: Optional[Department] = db.query(Department) \
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
