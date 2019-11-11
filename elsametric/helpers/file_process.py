import io
import json
from pathlib import Path
from typing import Tuple

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

from .helpers import data_inspector
from .paper_process import paper_process


def file_process(db: Session, file_path: Path, retrieval_time: str,
                 encoding: str = 'utf8') -> Tuple[dict, list]:
    """Reads a JSON formatted file and creates 'Paper' objects from it

    This function is the upstream of the 'paper_process' function. It
    reads a JSON formatted file located on 'file_path' using 'encoding'
    and then tries to create 'Paper' objects from it using the following
    steps for each entry:
        1. Inspect the entry for possible issues such as lack of 'paper
        title', or Scopus ID. If there are any issues, the 'bad_papers'
        list will be updated with the details of those issues.
        2. Decide if the issues are minor or major. Major ones will stop
        the program from successfully create a Paper object. Some of
        these issues include lack of Scopus ID, 'author', and
        'affiliation' data. Minor issues are the missing data points
        which can be safely replaced with default values; like 'paper
        title' or 'source title', which are replaced with a default
        value later on. Another example is the 'open access' status of
        the paper, which will be defaulted to '0' (closed access).
        3. After ignoring the minor issues, if there are any issues
        left, they would be considered as major and would cause the
        function to seek out the next paper within the file to process.
        If however, there are no remaining issues, the function will
        attempt to call the 'paper_process' function.
        4. After iterating through all entries within the file, the
        function will return a tuple containing a dict of bad_papers
        along with the file_path, and the list of created 'Paper'
        objects. If there is an exception, the function will create a
        report and returns it in a tuple along with an empty list (for
        Paper objects).

    Parameters:
        db: a Session instance of SQLAlchemy session factory to
            interact with the database
        file_path (Path): the path to a JSON formatted file exported
            from Scopus API containing information about some papers
        retrieval_time (str): a 'datatime' string pointing to the time
            that the data was retrieved from the Scopus API
        encoding (str): encoding to be used when reading the JSON file

    Returns:
        tuple: a tuple containing a dictionary of problems encountered
            when processing the papers and a list of 'Paper' objects
    """

    papers_list = []  # a list of 'Paper' objects to be added to the database
    bad_papers = []  # a list of all papers with issues
    minor_issues = [
        'eid', 'dc:title', 'subtype', 'author-count', 'openaccess',
        'citedby-count', 'source-id', 'prism:publicationName', 'author:afid']

    with io.open(file_path, 'r', encoding=encoding) as raw_file:
        data = json.load(raw_file)

    data = data['search-results']['entry']
    for cnt, entry in enumerate(data):
        issues = data_inspector(entry)
        if issues:
            # Before doing anything, submit the issues to be logged.
            bad_papers.append({'#': cnt, 'issues': [*issues]})

            if 'dc:identifier' in issues:
                # Paper has no Scopus ID, this is a serious problem!
                # The only way around it is to use 'eid' (if available):
                # eid = 2-s2.0-{Scopus ID}
                if 'eid' in issues:  # 'eid' also not found: can't go on
                    continue

                try:
                    # possible AttributeError, ValueError
                    paper_id_scp = int(entry['eid'].replace('2-s2.0-', ''))

                    # Form the 'dc:identifier' key from paper_id_scp
                    entry['dc:identifier'] = f'SCOPUS_ID:{paper_id_scp}'
                    issues.remove('dc:identifier')  # Issue dealt with.
                except (AttributeError, ValueError):
                    # Could not create 'dc:identifier' from 'eid'
                    continue

            bad_papers[-1]['id_scp'] = entry['dc:identifier']

            # Minor issues won't cause any problem for program's flow. Let's
            # filter them out.
            issues = [i for i in issues if i not in minor_issues]
            if issues:  # Any remaining issues are major: can't go on.
                continue

        # At this point, we have no major issues. The program should be able to
        # process the data. If any exceptions occured, we'll catch them below:
        try:
            papers_list.append(paper_process(db, entry, retrieval_time))
        except Exception as e:
            # Since 'paper_process' uses functions of its own, the type of
            # the exception cannot be easily determined.
            try:
                # possible IndexError
                if bad_papers[-1]['id_scp'] != entry['dc:identifier']:
                    raise ValueError
            except (IndexError, ValueError):  # This is the first bad_paper
                bad_papers.append(
                    {'#': cnt, 'id_scp': entry['dc:identifier']})
            finally:
                bad_papers[-1] = {
                    **bad_papers[-1],
                    'error_type': type(e),
                    'error_msg': str(e)
                }

    problems = {}
    if bad_papers:
        problems = {
            # mask the absolute path
            'file': str(file_path.relative_to(Path.cwd())),
            'papers': bad_papers
        }
    return problems, papers_list
