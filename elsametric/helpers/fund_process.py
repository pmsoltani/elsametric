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


def fund_process(db: Session, data: dict) -> Optional[Fund]:
    """Returns a single Source object to be added to a Paper object

    Receives a dictionary containing information about a paper and
    extracts the paper's funding info from it.

    Funding data from the Scopus API has 3 keys:
        fund-no: a code-like string
        fund-sponsor: the name of the funding agency
        fund-acr: the acronym of the funding agency

    Each of these can be absent from the data. An agency can have many
    funds and a fund-no can belong to multiple agencies. This means that
    the database cannot have a unique constrain on any columns, alone.

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        data (dict): a pre-checked dictionary containing information
            about a paper registered in the Scopus database

    Returns:
        Fund: a 'Fund' object to be added to a 'Paper' object
    """

    fund: Optional[Fund] = None

    fund_id_scp = get_key(data, 'fund-no')
    agency = get_key(data, 'fund-sponsor', default='NOT AVAILABLE')
    agency_acronym = get_key(data, 'fund-acr')
    if fund_id_scp == 'undefined':
        fund_id_scp = 'NOT AVAILABLE'
    # DBMSs' Unique Constraints accept rows with one column being null and the
    # other have repeated values. So we must change None to 'NOT AVAILABLE'.

    if (fund_id_scp == 'NOT AVAILABLE') and (agency == 'NOT AVAILABLE'):
        # Both 'fund_id_scp' & 'agency' are 'NOT AVAILABLE'. Can't go on.
        return fund

    fund = db.query(Fund) \
        .filter(Fund.id_scp == fund_id_scp, Fund.agency == agency) \
        .first()

    if not fund:
        fund = Fund(
            id_scp=fund_id_scp, agency=agency, agency_acronym=agency_acronym)

    return fund
