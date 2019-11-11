from typing import List, Optional, Tuple

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

from .helpers import get_key
from .institution_process import institution_process


def author_process(db: Session, data: dict) -> List[Tuple[int, Author]]:
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
    author_base_url = 'https://www.scopus.com/authid/detail.uri?authorId='

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
                address=f'{author_base_url}{author_id_scp}',
                type='Scopus Profile',
            )
            author.profiles.append(author_profile)

        # Get a list of all Institution IDs for the author in the paper
        inst_ids = get_key(auth, 'afid', many=True, default=[])
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

        authors_list.append((author_no, author))
    return authors_list
