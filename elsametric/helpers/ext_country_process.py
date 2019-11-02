from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from .helpers import country_names, get_row, nullify

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


def ext_country_process(
        db: Session, file_path: Path,
        encoding: str = 'utf-8-sig') -> List[Country]:
    """Imports a list of countries to database

    Reads a .csv file and creates 'Country' objects which represent
    rows in the 'country' table in the database. Each country object
    should have the following attributes:
        name: full name of the country
        domain: the 2-character code of the country (ISO 3166-1 alpha-2)
        region: the continent of the country
        sub_region: general geo-graphical location of the country

    It is assumed that each row of the .csv file contains these parts.

    Dependencies(libraries):
        io, csv

    Dependencies(functions):
        nullify: changes any null-looking value to None
        country_names: assigns a unified name to countries with name
            variations

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        file_path (Path): the path to a .csv file containing a list of
            country names with details
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        list: a list of 'Country' objects to be added to the database
    """

    countries_list = []
    rows = get_row(file_path, encoding)
    for row in rows:
        nullify(row)
        country_name = country_names(row['name']).strip()
        country: Optional[Country] = db.query(Country) \
            .filter(Country.name == country_name) \
            .first()
        if not country:  # 'country' not in database, let's create it.
            country = Country(
                name=country_name,
                domain=row['domain'].strip(),
                region=row['region'].strip(),
                sub_region=row['sub_region'].strip()
            )
            countries_list.append(country)
    return countries_list
