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
