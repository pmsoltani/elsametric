from typing import Optional

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

from .helpers import get_key, nullify, strip
from .author_process import author_process
from .fund_process import fund_process
from .keyword_process import keyword_process
from .source_process import source_process


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

            # There is at least one case that two different papers in the
            # Scopus database had the same DOI (but different Scopus IDs:
            # 84887280754 & 84887287423, as of Oct. 31, 2019), which led
            # the algorithm to come to this point).
            if paper and paper.title != paper_title:
                paper = None  # So that we can create it in the next 'if'
                paper_doi = None  # Avoid violating DB's unique constraint

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
                get_key(data, 'prism:volume'), accepted_chars='', max_len=45),
            issue=get_key(data, 'prism:issueIdentifier'),
            date=get_key(data, 'prism:coverDate'),
            page_range=get_key(data, 'prism:pageRange'),
            retrieval_time=retrieval_time,
        )

    # Setting additional data
    paper.source = paper.source or source_process(db, data)
    paper.fund = paper.fund or fund_process(db, data)
    paper.keywords = paper.keywords or keyword_process(db, data)

    if not paper.authors:
        authors_list = author_process(db, data)
        for author in authors_list:
            # Using the SQLAlchemy's Association Object to add paper's authors.
            paper_author = Paper_Author(author_no=author[0])
            paper_author.author = author[1]
            paper.authors.append(paper_author)
    # The reported count of authors from Scopus can't be trusted: set it here.
    paper.total_author = len(paper.authors)

    return paper
