def country_names(name: str):
    """Changes the name of some countries to pre-defined values

    Parameters:
        name (str): the name of the country to be inspected

    Returns:
        str: the new name of the country
    """

    countries = {
        'Russian Federation': 'Russia',
        'USA': 'United States',
        'Great Britain': 'United Kingdom',
        'Vietnam': 'Viet Nam',
        'Zweden': 'Sweden',
        'Czech Republic': 'Czechia',
    }
    if name in countries.keys():
        return countries[name]
    return name


def data_inspector(data: dict, keys):
    """Inspects the Scopus API data for possible issues

    The function traverses through the data provided by the Scopus API
    and looks for important keys that are missing. These are mentioned
    in the 'first_level_keys' list. Any missing key will be added as an
    issue to the 'issues' list.

    Some of the keys in the data are themselves dictionaries or lists of
    dictionaries. For these, a second level inspection is performed and
    if there are any keys missing, those will be added to the 'issues'
    list as well.

    Parameters:
        data (dict): the dictionary to be inspected for issues
        keys: the keys of the dictionary

    Returns:
        list: the list of issues of the data
    """

    issues = []
    first_level_keys = [
        'source-id',
        'prism:publicationName',
        'prism:coverDate',
        'dc:identifier',
        'eid',
        'dc:title',
        'subtype',
        'author-count',
        'openaccess',
        'citedby-count',
        'link',
        'author',
        'affiliation',
    ]
    author_keys = ['authid', '@seq', 'afid']
    affiliation_keys = ['afid', 'affilname']

    # first level inspection
    for key in first_level_keys:
        if key not in keys:
            issues.append(key)

    # second level inspections
    if 'link' not in issues:
        # The 'link' key might be in the data, but it may not have the
        # paper's url (denoted by 'scopus' tag) inside it.
        if all(link['@ref'] != 'scopus' for link in data['link']):
            issues.append('paper url')

    # The 'author' and 'affiliation' keys might be in the data, but we
    # must make sure that they have all the second level keys mentioned
    # by the 'author_keys' and 'affiliation_keys' respectively.
    if 'author' not in issues:
        for author in data['author']:
            keys = author.keys()
            for key in author_keys:
                if key not in keys:
                    issues.append(f'author:{key}')
    if 'affiliation' not in issues:
        for affiliation in data['affiliation']:
            keys = affiliation.keys()
            for key in affiliation_keys:
                if key not in keys:
                    issues.append(f'affiliation:{key}')

    # check for the presence of the '$' key and its value inside 'author-count':
    if 'author-count' not in issues:
        if '$' not in data['author-count'].keys():
            issues.append('author-count')
        else:
            if not data['author-count']['$']:
                issues.append('author-count')

    return issues


def key_get(data: dict, keys, key: str, many: bool = False, default=None):
    """Retrieves the value of a certain key inside a dictionary

    The function is designed to traverse a dictionary and retrieve the
    value of the 'key' parameter inside that dictionary. If the 'key' is
    not found, or if its value is null, the 'default' value will be
    returned.

    If the value is a list, the function will return the value of the
    '$' key inside the first element, or all of the '$' values, based on
    the state of the 'many' parameter (returns a set).

    If the value is a dict, the function will return the value for the
    '$' key inside that dict.

    Parameters:
        data (dict): a dict containing the desired (key, value) pair
        keys: the keys of the data, passed to avoid repeated evaluation
        key (str): the desired key within the dictionary
        many (bool): if True, makes the function to return a list
        default: the return value for when the key not found in the
            dictionary or if it is null

    Returns:
        the value of the 'key' in the dictionary, or the 'default' value
    """

    result = None
    if key in keys:
        result = data[key]

    if result is None:
        return default

    if isinstance(result, list):
        if not many:  # return only the first item
            return result[0]['$']
        return {item['$'] for item in result}  # return a set of all items

    if isinstance(result, dict):
        return result['$']

    # the result is neither a list nor a dict and it's not None
    return result


def nullify(data: dict, null_types: tuple = (None, '', ' ', '-', '#N/A')):
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


def strip(string, accepted_chars: str = '0123456789xX', max_len: int = 0):
    """Strips a string from unwanted characters

    Parameters:
        string: the string to be stripped from unwanted characters
        accepted_chars (str): a string consisted of the characters that
            are accepted in the return string; an empty string means all
            characters are accepted
        max_len (int): maximum length allowed for the return string

    Returns:
        str: a string that is stripped from unwanted characters
    """

    if not string:  # do nothing
        return string

    if accepted_chars:
        stripped = ''.join([c for c in string.strip() if c in accepted_chars])
    else:  # all chars are accepted
        stripped = string.strip()

    if max_len:  # force truncate the string
        return stripped[:max_len]
    return stripped
