from pathlib import Path
from typing import Iterator, List, Optional

from sqlalchemy.orm import Session

from .helpers import get_key, get_row, nullify, strip

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


def ext_source_metric_process(
        db: Session, file_path: Path, file_year: int,
        encoding: str = 'utf-8-sig') -> Iterator[Source]:

    subjects: List[Subject] = db.query(Subject).all()
    # Turn 'subjects' which is a list of 'Subject' objects, into a dict:
    # {asjc1: Subject1, asjc2: Subject2, ...}
    subjects = {subject.asjc: subject for subject in subjects}

    metric_types = {
        'citescore': 'CiteScore',
        'percentile': 'Percentile',
        'snip': 'SNIP',
        'sjr': 'SJR',
        'citations': 'Citations',
        'documents': 'Documents',
        'percent_cited': 'Percent Cited',
    }

    rows = get_row(file_path, encoding)
    for row in rows:
        nullify(row)
        try:
            source_id_scp = int(row['id_scp'])  # possible TypeError
        except TypeError:
            continue

        source: Optional[Source] = db.query(Source) \
            .filter(Source.id_scp == source_id_scp) \
            .first()

        source_publisher = get_key(row, 'publisher')
        if not source:  # 'source' not in database, let's create it.
            source = Source(
                id_scp=source_id_scp,
                title=get_key(row, 'title', default='NOT AVAILABLE'),
                type=get_key(row, 'type'),
                issn=strip(get_key(row, 'issn'), max_len=8),
                e_issn=strip(get_key(row, 'e_issn'), max_len=8),
            )

        # Setting additional source info if it does not exist already.
        source.publisher = source.publisher or source_publisher

        if source_publisher and not source.country:
            # Try to find country using publisher data of other sources:
            try:
                country: Optional[Country] = db.query(Source) \
                    .filter(
                        Source.publisher == source_publisher,
                        Source.country != None) \
                    .first().country  # possible AttributeError
                source.country = country
            except AttributeError:  # 'country' not found.
                pass

        if row['asjc'] and not source.subjects:
            asjc = int(row['asjc'])
            try:
                source.subjects.append(subjects[asjc])
            except KeyError:  # 'asjc' not found in the database (unlikely).
                pass

        # Processing metrics
        # Creating a dict out of metrics already attached to the source:
        source_metrics = {}
        for metric in source.metrics:
            if metric.year == file_year:
                source_metrics[metric.type] = metric

        for metric in metric_types:
            try:
                metric_value = float(row[metric])
            except (KeyError, TypeError, ValueError):  # value not available
                continue
            # Using pre-defined names for metrics:
            metric = metric_types[metric]
            if metric not in source_metrics:
                source.metrics.append(
                    Source_Metric(
                        type=metric, value=metric_value, year=file_year))

        yield source
