from typing import List, Optional

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

from .helpers import get_key, strip


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
