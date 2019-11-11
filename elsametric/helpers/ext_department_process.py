from pathlib import Path

from .helpers import get_row


def ext_department_process(
        file_path: Path, encoding: str = 'utf-8-sig') -> dict:
    """Returns a dictionary of department data

    This function is a helper tool for the function ext_faculty_process.
    It returns a dictionary of department data which will be used to
    assign the departments of each faculty member in the institution.

    Parameters:
        file_path (Path): the path to a .csv file containing a list of
            faculties along with some details
        encoding (str): encoding to be used when reading the .csv file

    Returns:
        dict: a dictionary with the following format:
            {dept_abbreviation: {name: dept_full_name, type: dept_type}}
    """

    departments = {}
    rows = get_row(file_path, encoding)
    for row in rows:
        departments[row['Department Abbreviation']] = {
            'name': row['Department En'], 'type': row['Type']}
    return departments
