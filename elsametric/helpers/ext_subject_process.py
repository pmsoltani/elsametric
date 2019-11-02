from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from .helpers import get_row, nullify

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
