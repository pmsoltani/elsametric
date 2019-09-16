from fastapi import FastAPI

from api_queries import authors_list_frontend, get_author

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
    response = {'key': f"all of {id_frontend}'s papers"}
    return response


@app.get('/a/{id_frontend}/trend')
async def show_author(id_frontend: str, year: int = None):
    response = {'key': f"{id_frontend}'s yearly papers and citations count"}
    if year:
        response = {
            'key': f"{id_frontend}'s papers for the specified year: {year}"}
    return response


@app.get('/a/{id_frontend}/network')
async def show_author(id_frontend: str, co_id: str = None):
    response = {'key': f"all of {id_frontend}'s collaborators"}
    if co_id:
        response = {
            'key': f"all of {id_frontend}'s papers with collaborator: {co_id}"}
    return response


@app.get('/a/{id_frontend}/keywords')
async def show_author(id_frontend: str, tag: str = None):
    response = {'key': f"all of {id_frontend}'s keywords"}
    if tag:
        response = {
            'key': f"all of {id_frontend}'s papers with keyword: {tag}"}
    return response


@app.get('/a/{id_frontend}/journals')
async def show_author(id_frontend: str, rank: str = None):
    response = {'key': f"all of {id_frontend}'s journal Qs"}
    if rank:
        response = {
            'key': f"all of {id_frontend}'s papers in {rank} journals"}
    return response
