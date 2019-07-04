def data_inspector(data:dict):
    warnings = []
    top_keys = [
        'source-id', 'prism:publicationName', 'prism:coverDate',
        'dc:identifier', 'eid', 'dc:title', 'subtype', 'author-count',
        'openaccess', 'citedby-count', 'link',
        'author', 'affiliation',
    ]
    author_keys = ['authid', '@seq', 'afid']
    affiliation_keys = ['afid', 'affilname']

    keys = data.keys()
    for key in top_keys:
        if key not in keys:
            warnings.append(key)
    if 'link' not in warnings:
        if all(link['@ref'] != 'scopus' for link in data['link']):
            warnings.append('paper url')
    if 'author' not in warnings:
        for author in data['author']:
            keys = author.keys()
            for key in author_keys:
                if key not in keys:
                    warnings.append(f'author:{key}')
    if 'affiliation' not in warnings:
        for affiliation in data['affiliation']:
            keys = affiliation.keys()
            for key in affiliation_keys:
                if key not in keys:
                    warnings.append(f'affiliation:{key}')
    return warnings


def key_get(data:dict, keys, key:str, many:bool=False):
    if key in keys:
        result = data[key]
    else:
        result = None
    
    if type(result) == list:
        if not many:
            return result[0]['$']
        return [int(item['$']) for item in result]
    if type(result) == dict:
        return result['$']
    return result


def strip(data, max_length:int=8, accepted_chars:str='0123456789xX', force_strip:bool=True):
    if not data:
        return data
    if not accepted_chars:
        return data.strip()[:max_length]
    if force_strip:
        return ''.join([char for char in data if char in accepted_chars])[:max_length]
    return ''.join([char for char in data if char in accepted_chars])


def country_names(name):
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


def nullify(data:dict, null_types:list=[None, '', ' ', '-']):
    for key in data:
        if data[key] in null_types:
            data[key] = None

