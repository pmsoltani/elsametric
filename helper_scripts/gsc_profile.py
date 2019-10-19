import io
import csv
import json
import time
import scholarly
from pathlib import Path

from helpers import get_row, exporter, new_columns, gsc_metrics


# ==============================================================================
# Config
# ==============================================================================


CURRENT_DIR = Path.cwd()
with io.open(CURRENT_DIR / 'crawlers_config.json', 'r') as config_file:
    config = json.load(config_file)

gsc_config = config['google_scholar']
inst_config = config['institutions']

BASE = gsc_config['base_url']

METRICS_EXPIRATION = gsc_config['metrics_expiration_days']
COLUMNS = [f'Google Scholar {i}'
           for i in ['ID', 'Name', 'h-index', 'i10-index', 'Retrieval Time']]


# ==============================================================================
# Script
# ==============================================================================


# This script can process authors from multiple institutions, separately
for institution in inst_config:
    if not inst_config[institution]['process']:
        continue

    # --------------------------------------------------------------------------
    # Institution-Level config
    # --------------------------------------------------------------------------

    HEADERS = {'User-Agent': inst_config[institution]['user_agent']}
    DATA_PATH = CURRENT_DIR / inst_config[institution]['data_directory']
    EXPORT_FILE = f'{institution}_faculties_with_gsc.csv'
    EXPORT_PATH = DATA_PATH / EXPORT_FILE
    FIRST_AUTHOR_ID = inst_config[institution]['first_faculty_id']

    rows = get_row(DATA_PATH / inst_config[institution]['faculties'])
    first_author_crawled = not FIRST_AUTHOR_ID or False  # no config: crawl all
    csv_headers = not Path(EXPORT_PATH).is_file()

    # --------------------------------------------------------------------------
    # Main script
    # --------------------------------------------------------------------------

    for row in rows:
        print(f'{institution}: {row["Institution ID"]} ...', end=' ')
        new_columns(row, COLUMNS, None)

        if row['Institution ID'] == FIRST_AUTHOR_ID:  # 1st author reached
            first_author_crawled = True
        if not first_author_crawled:  # 1st author (config) not reached yet
            print('skipping (config)')
            continue

        if not row['Google Scholar ID']:  # find gsc_id using 'scholarly'
            query = [row["First En"], row["Last En"], institution]

            # query with high specificity
            author = next(scholarly.search_author(' '.join(query)), None)
            if not author:
                # no results, trying query with lower specificity (without the
                # institution name)
                author = next(
                    scholarly.search_author(' '.join(query[: -1])),
                    None
                )
            if not author:
                print('profile not found')
                exporter(EXPORT_PATH, [row], headers=csv_headers)
                csv_headers = False
                continue
            row['Google Scholar ID'] = author.id
            row['Google Scholar Name'] = author.name

        time_diff = 0
        try:
            last_update = int(row['Google Scholar Retrieval Time'])
            time_diff = (time.time() - last_update) / (3600 * 24)  # days since
        except (KeyError, ValueError, TypeError):
            pass

        # metrics do not exist or are old
        if not(time_diff) or time_diff > METRICS_EXPIRATION:
            h_index, i10_index = gsc_metrics(
                BASE, row['Google Scholar ID'], HEADERS)
            row['Google Scholar h-index'] = h_index
            row['Google Scholar i10-index'] = i10_index
            row['Google Scholar Retrieval Time'] = int(time.time())

        print('done')
        exporter(EXPORT_PATH, [row], headers=csv_headers)
        csv_headers = False
