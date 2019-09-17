from fastapi import FastAPI

from api_queries import authors_list_frontend, get_author, get_author_papers, \
    get_author_trend, get_author_keywords, get_author_journals, \
    get_author_network

app = FastAPI()


@app.get('/')
async def home():
    return {'key': 'Visit list', 'url': 'http://127.0.0.1:8000/a/list'}


@app.get('/a/list')
async def show_authors_list(inst_fid: str = None):
    # response = {'key': 'list of all authors in the db'}
    response = authors_list_frontend
    if inst_fid:
        response = {'key': f'FEATURE !READY: list of all authors in {inst_fid}'}
    return response


@app.get('/a/{id_frontend}')
async def show_author(id_frontend: str):
    response = get_author(id_frontend)
    return response


@app.get('/a/{id_frontend}/papers')
async def show_author(id_frontend: str):
    response = get_author_papers(id_frontend)
    return response


@app.get('/a/{id_frontend}/trend')
async def show_author(id_frontend: str, year: int = None):
    response = get_author_trend(id_frontend)
    if year:
        response = get_author_papers(id_frontend, year)
    return response


@app.get('/a/{id_frontend}/network')
async def show_author(id_frontend: str, co_id: str = None):
    response = get_author_network(id_frontend)
    if co_id:
        response = {
            'key': f"all of {id_frontend}'s papers with collaborator: {co_id}"}
    return response


@app.get('/a/{id_frontend}/keywords')
async def show_author(id_frontend: str, tag: str = None):
    response = get_author_keywords(id_frontend)
    if tag:
        response = get_author_keywords(id_frontend, keyword=tag)
    return response


@app.get('/a/{id_frontend}/journals')
async def show_author(id_frontend: str, q: str = None):
    response = get_author_journals(id_frontend)
    if q:
        response = get_author_journals(id_frontend, q)
    return response
