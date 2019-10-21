import io
import csv
from typing import Tuple
import requests as req
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz


def get_row(path: str, encoding: str = 'utf-8', delimiter: str = ','):
    """Yields a row from a .csv file

    This simple function is used to yield a .csv file in 'path',
    row-by-row, so as not to consume too much memory.

    Parameters:
        path (str): the path to the .csv file
        encoding (str): encoding to be used when reading the .csv file
        delimiter (str): the delimiter used in the .csv file

    Yields:
        row: a row of the .csv file
    """

    with io.open(path, 'r', encoding=encoding) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        for row in reader:
            yield row


def exporter(path: str, rows: list,
             reset: bool = False, bulk: bool = False, headers: bool = False,
             encoding='utf-8', delimiter=',', lineterminator='\n'):
    """Exports a list of dictionaries to a .csv file

    The function receives a list of dictionaries, 'rows', and attempt to
    write them to a file specified by 'path', according to the other
    parameters provided.

    Parameters:
        path (str): the path to the .csv file
        rows (list): the list of dictionaries to be written
        reset (bool): whether to write to the file from the beginning or
        append to it
        bulk (bool): whether to write the whole list or just the
        last row
        headers (bool): whether to create a headers row or not
        encoding (str): encoding to be used when writing the .csv file
        delimiter (str): the delimiter used in the .csv file
        lineterminator (str): the line ending used in the .csv file

    Returns:
        None
    """

    if not rows:
        return

    rows_key_count = [len(row.keys()) for row in rows]
    row_with_max_keys = rows_key_count.index(max(rows_key_count))

    with io.open(path, 'a' if not reset else 'w', encoding=encoding) as file:
        writer = csv.DictWriter(file, fieldnames=rows[row_with_max_keys].keys(),
                                delimiter=delimiter,
                                lineterminator=lineterminator)

        if headers:
            writer.writeheader()

        if bulk:
            writer.writerows(rows)  # write to the csv file all at once
        else:
            writer.writerows(rows[-1:])  # write to the csv file row-by-row


def nullify(data: dict, null_types: tuple = ('', ' ', '-', '#N/A', '---')):
    """Changes the null-looking values in a dictionary to None in-place

    The function receives a dictionary and looping through its items. If
    an item has a null-looking value (defined by the 'null_types'
    tuple), it will be changed (in-place) to None. This is so that the
    database receiving the values could stay clean.

    Parameters:
        data (dict): the dictionary to be processed for its null values
        null_types (tuple): a tuple of values that resemble null
    """

    for key in data:
        if data[key] in null_types:
            data[key] = None


def upper_first(string: str) -> str:
    """Changes the first letter of a name to uppercase

    This simple function receives a string (a name) and changes the 1st
    letter of that name to uppercase. Python's str.title() method does
    this with an important difference: it changes the rest of the name's
    letters to lowercase, which in some cases might be a bad idea.

    Parameters:
        string (str): the string to be manipulated

    Returns:
        the same string with its first letter changed to uppercase
    """

    if not string or not isinstance(string, str):
        return string
    return string[0].upper() + string[1:]


def new_columns(data: dict, columns: list, init_value):
    """Initializes new columns to the provided table

    The function receives a dictionary (the table), a list (the columns)
    and an initial value. Then, it adds all columns that are not already
    present in the table, using the initial value.

    This function can help to export a more uniform csv table, by making
    all rows have the same columns.

    Parameters:
        data (dict): the dictionary (table) to be expanded with new cols
        columns (list): the list of columns to be added to the dict
        init_value (): the value to initialize the new columns with

    Returns:
        the same string with its first letter changed to uppercase
    """

    if not isinstance(data, dict):
        return data

    for column in columns:
        if column not in data.keys():  # skip already present columns
            data[column] = init_value


def gsc_metrics(base_url: str, gsc_id: str, headers: dict = {}):
    """Retrieves h-index & i10-index metrics from google scholar

    The function attempts to retrieve the h-index & i10-index of an
    author (gsc_id) from google scholar.

    The google scholar's base url and proper headers for making HTTP
    requests must also be provided to the function.

    Parameters:
        base_url (str): the base url of every google scholar profile
        gsc_id (str): the google scholar id of the author
        headers (dict): the headers for the 'requests' package to make
        HTTP requests

    Returns:
        h-index & i10-index of the author
    """

    params = {'user': gsc_id}
    h_index = i10_index = None
    try:
        page = req.get(base_url, headers=headers, params=params)
        page.raise_for_status()
        index_table = BeautifulSoup(page.content, 'html.parser') \
            .find('table', attrs={'id': 'gsc_rsb_st'})
    except (AttributeError, req.HTTPError):
        return h_index, i10_index

    try:
        h_index = index_table.find('td', string='h-index').find_next('td')
        h_index = int(h_index.text)
    except (ValueError, AttributeError):
        pass

    try:
        i10_index = index_table.find('td', string='i10-index').find_next('td')
        i10_index = int(i10_index.text)
    except (ValueError, AttributeError):
        pass

    return h_index, i10_index


def author_faculty_matcher(authors: list, first: str, last: str, initials: str,
                 cutoff: int) -> Tuple[list, str]:
    """Attemps to match the provided names with a list of authors

    This function uses different methods (with different levels of
    certainties) to match the provided 'first', 'last', and 'initials'
    to a list of elsametric 'author' objects. The methods are sorted by
    their level of confidence and if the names are matched, the function
    returns a list of Scopus IDs, along with the confidence level.

    If no methods are able to match, an empty list and an empty string
    will be returned.

    Parameters:
        authors (list): a list of author objects, queried from database
        first (str): first name of the faculty to be matched
        last (str): last name of the faculty to be matched
        initials (str): initials of the faculty to be matched
        cutoff (int): indicates how high the score of fuzzy-matching
        should be for the strings considered to be the same

    Returns:
        (list, str): a list of Scopus IDs and a level of confidence
    """

    # High confidence: first name (exact) & last name (exact) -> 100%
    matches = [author.id_scp for author in authors
               if author.last == last and author.first == first]
    if matches:
        return matches, 'High'

    # Medium confidence: initials (exact) & last name (exact)
    matches = []
    for author in authors:
        try:
            if author.last == last and author.first[0] == initials:
                matches.append(author.id_scp)
        except TypeError:  # author did not have a first name
            continue
    if matches:
        return matches, 'Medium'

    # Medium confidence: first name(fuzzy) & last name(exact) -> 80%
    matches = []
    for author in authors:
        condition_first = fuzz.partial_ratio(author.first, first) >= cutoff
        if author.last == last and condition_first:
            matches.append(author.id_scp)
    if matches:
        return matches, 'Medium'

    # Low confidence: first name (fuzzy) & last name (fuzzy) -> 64%
    matches = []
    for author in authors:
        condition_first = fuzz.partial_ratio(author.first, first) >= cutoff
        condition_last = fuzz.partial_ratio(author.first, last) >= cutoff
        if condition_first and condition_last:
            matches.append(author.id_scp)
    if matches:
        return matches, 'Low'

    # None of the above method worked
    return [], ''
