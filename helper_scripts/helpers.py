import io
import csv


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


def exporter(path: str, rows: list, all_rows: bool = False, headers: bool = False):
    with io.open(path, 'a' if not all_rows else 'w', encoding='utf-8') as file:
        writer = csv.DictWriter(
            file, rows[0].keys(), delimiter=',', lineterminator='\n'
        )
        if headers or all_rows:
            writer.writerow(dict((fn, fn) for fn in rows[0].keys()))
        if all_rows:
            writer.writerows(rows)  # write to the csv file all at once
        writer.writerows(rows[-1:])  # write to the csv file row-by-row


def nullify(data: dict, null_types: tuple = (None, '', ' ', '-', '#N/A', '---')):
    """Changes the null-looking values in a dictionary to None

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
