from pathlib import Path
from typing import Iterator, List, Optional

from sqlalchemy.orm import Session

from .helpers import country_names, get_key, get_row, nullify

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


def ext_source_process(
        db: Session, file_path: Path, src_type: Optional[str] = None,
        encoding: str = 'utf-8-sig') -> Iterator[Source]:
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

        # 'source' not in database, let's create it:
        source = Source(
            id_scp=source_id_scp,
            title=get_key(row, 'title', default='NOT AVAILABLE'),
            type=get_key(row, 'type') or src_type,
            issn=get_key(row, 'issn'),
            e_issn=get_key(row, 'e_issn'),
            publisher=get_key(row, 'publisher')
        )
        # Adding country info to the source:
        country_name = country_names(get_key(row, 'country'))
        if country_name:
            country = db.query(Country) \
                .filter(Country.name == country_name) \
                .first()
            source.country = country  # 'country' either found or None.

        # Adding subject info to the source:
        raw_asjc_codes = get_key(row, 'asjc', default='')  # '' if not found.
        # Creating a set of unique asjc codes:
        asjc_codes = {code.strip()
                      for code in raw_asjc_codes.split(';') if code.strip()}
        for code in asjc_codes:
            try:
                # possible ValueError, KeyError
                subject = subjects[int(code)]
                source.subjects.append(subject)
            except (ValueError, KeyError):
                continue

        yield source
