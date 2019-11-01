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
            raw_keyword = raw_keyword.strip()
            if raw_keyword and raw_keyword.lower() not in unique_keys_set:
                unique_keys_set.add(raw_keyword.lower())
                keywords.append(raw_keyword)

        # At this point, all keywords are stripped and unique within the paper.
        for raw_keyword in keywords:
            keyword: Optional[Keyword] = db.query(Keyword) \
                .filter(Keyword.keyword == raw_keyword) \
                .first()
            if not keyword:  # Keyword not in database, let's add it.
                keyword = Keyword(keyword=raw_keyword)
            keywords_list.append(keyword)

    return keywords_list
