import io
import csv
import json
import time
import scholarly
import requests as req
from bs4 import BeautifulSoup
from pathlib import Path


# ==============================================================================
# Config
# ==============================================================================


current_dir = Path.cwd()
config_path = current_dir / 'config.json'
with io.open(config_path, 'r') as config_file:
    config = json.load(config_file)

config = config['database']['populate']
data_path = config['data_directory']
metrics_expiration = config['metrics_expiration_days']


# ==============================================================================
# Helper functions
# ==============================================================================


def get_row(file_path: str, encoding: str = 'utf-8-sig', delimiter: str = ','):
    """Yields a row from a .csv file

    This simple function is used to yield a .csv file in 'file_path',
    row-by-row, so as not to consume too much memory.

    Parameters:
        file_path (str): the path to the .csv file
        encoding (str): encoding to be used when reading the .csv file
        delimiter (str): the delimiter used in the .csv file

    Yields:
        row: a row of the .csv file
    """

    with io.open(file_path, 'r', encoding=encoding) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        for row in reader:
            yield row


def get_metrics(gsc_id: str):
    base = 'https://scholar.google.com/citations'
    params = {'user': gsc_id}
    agt = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'
    headers = {'User-Agent': agt}
    page = req.get(base, headers=headers, params=params)

    soup = BeautifulSoup(page.content, 'html.parser')
    index_table = soup.find('table', attrs={'id': 'gsc_rsb_st'})
    try:
        h_index = index_table.find('td', string='h-index').find_next('td')
        h_index = int(h_index.text)
    except (ValueError, AttributeError):
        h_index = None

    try:
        i10_index = index_table.find('td', string='i10-index').find_next('td')
        i10_index = int(i10_index.text)
    except (ValueError, AttributeError):
        i10_index = None

    return h_index, i10_index


def exporter(file_path: str, rows: list, all_rows: bool = False):
    with io.open(file_path, 'a' if not all_rows else 'w', encoding='utf-8') as file:
        writer = csv.DictWriter(
            file, rows[0].keys(), delimiter=',', lineterminator='\n'
        )
        writer.writerow(dict((fn, fn) for fn in rows[0].keys()))
        if all_rows:
            writer.writerows(rows)  # write to the csv file all at once
        writer.writerows(rows[-1:])  # write to the csv file row-by-row


# ==============================================================================
# Script
# ==============================================================================


for item in config['institutions']:
    if not item['process']:
        continue
    institution = item["name"]
    rows = get_row(current_dir / data_path / item['faculties'])

    export_file = f'{institution}_faculties_with_gsc_{int(time.time())}.csv'
    export_path = current_dir / data_path / export_file

    for row in rows:
        print(f'Processing: {row["Institution ID"]}...', end=' ')
        if (
            ('Google Scholar ID' not in row.keys()) or
            (not row['Google Scholar ID'])
        ):
            query = [row["First En"], row["Last En"], institution]

            # query with high specificity
            author = next(scholarly.search_author(' '.join(query)), None)
            if not author:
                # no results, trying query with lower specificity (without the
                # institution name)
                author = next(
                    scholarly.search_author(' '.join(query[:-1])),
                    None
                )
            if not author:
                print('profile not found')
                exporter(export_path, [row])
                continue
            row['Google Scholar ID'] = author.id
            row['Google Scholar Name'] = author.name

        time_diff = 0
        try:
            last_update = int(row['Google Scholar Retrieval Time'])
            time_diff = (time.time() - last_update) / (3600 * 24)
        except (KeyError, ValueError):
            pass

        if not(time_diff) or time_diff > metrics_expiration:
            row['Google Scholar h-index'],
            row['Google Scholar i10-index'] = get_metrics(
                row['Google Scholar ID'])
            row['Google Scholar Retrieval Time'] = int(time.time())

        print('done')
        exporter(export_path, [row])
