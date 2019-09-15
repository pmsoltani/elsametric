from fastapi import FastAPI

from api_queries import authors_list

app = FastAPI()


@app.get('/')
async def home():
    return {'key': 'Hello World!'}


@app.get('/a/list')
async def get_authors_list(inst_fid: str = None):
    # response = {'key': 'list of all authors in the db'}
    response = authors_list()
    if inst_fid:
        response = {'key': f'list of all authors in {inst_fid}'}
    return response


@app.get('/a/{auth_fid}')
async def get_author(auth_fid: str):
    response = {'key': f"{auth_fid}'s info (name, rank, contact, ...)"}
    return response


@app.get('/a/{auth_fid}/papers')
async def get_author(auth_fid: str):
    response = {'key': f"all of {auth_fid}'s papers"}
    return response


@app.get('/a/{auth_fid}/trend')
async def get_author(auth_fid: str, year: int = None):
    response = {'key': f"{auth_fid}'s yearly papers and citations count"}
    if year:
        response = {
            'key': f"{auth_fid}'s papers for the specified year: {year}"}
    return response


@app.get('/a/{auth_fid}/network')
async def get_author(auth_fid: str, co_id: str = None):
    response = {'key': f"all of {auth_fid}'s collaborators"}
    if co_id:
        response = {
            'key': f"all of {auth_fid}'s papers with collaborator: {co_id}"}
    return response


@app.get('/a/{auth_fid}/keywords')
async def get_author(auth_fid: str, tag: str = None):
    response = {'key': f"all of {auth_fid}'s keywords"}
    if tag:
        response = {
            'key': f"all of {auth_fid}'s papers with keyword: {tag}"}
    return response


@app.get('/a/{auth_fid}/journals')
async def get_author(auth_fid: str, rank: str = None):
    response = {'key': f"all of {auth_fid}'s journal Qs"}
    if rank:
        response = {
            'key': f"all of {auth_fid}'s papers in {rank} journals"}
    return response
