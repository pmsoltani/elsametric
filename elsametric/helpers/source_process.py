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
    if not source:  # 'source' not in database, let's create it.
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
