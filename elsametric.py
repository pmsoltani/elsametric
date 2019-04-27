import requests as req
import json

with open('config.json', 'r') as read_file:
    client = json.load(read_file)

# functions
def sc_query(inst: str, city: str, country: str, start_year: int, end_year: int = 0):
    inst_q = ' AND '.join(inst.lower().split(' '))
    city_q = ' AND '.join(city.lower().split(' '))
    country_q = ' AND '.join(country.lower().split(' '))
    return (
        f'AFFIL({inst_q}) AND '
        f'AFFILCITY({city_q}) AND '
        f'AFFILCOUNTRY({country_q}) AND '
        f'(PUBYEAR > {start_year - 1})'
    ) + (f' AND (PUBYEAR < {end_year + 1})' if end_year != 0 else '')

def sc_lookup(client:dict, query: str, cnt, start_cursor: int = 0, count_per_page: int = 25):
    base = 'https://api.elsevier.com/content/search/scopus'
    params = {
        'query': query,
        'apiKey': client['apikey'],
        'insttoken': client['insttoken'],
        'view': 'COMPLETE',
        'start': f'{start_cursor + (cnt * count_per_page)}',
        'count': f'{count_per_page}',
    }
    headers = {'Accept': 'application/json'}
    return req.get(url=base, params=params)

inst = 'university of tehran'
city = 'tehran'
country = 'iran'
start_year = 2019
query = sc_query(inst=inst, city=city, country=country, start_year=start_year)

res = sc_lookup(client=client, query=query, cnt=0)

# res.json()
titles = [doc['dc:title'] for doc in res.json()['search-results']['entry']]
for t in titles:
    print(t)
    print()