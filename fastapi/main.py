from fastapi import FastAPI

app = FastAPI()


@app.get('/')
async def home():
    return {'message': 'Hello World!'}


@app.get('/a/{author_front_id}')
async def get_author(author_front_id: str):
    response = {'key': f"all of {author_front_id}'s papers"}
    return response


@app.get('/a/{author_front_id}/summary')
async def get_author(author_front_id: str, year: int = None):
    response = {'key': f"{author_front_id}'s yearly papers and citations count"}
    if year:
        response = {
            'key': f"{author_front_id}'s papers for the specified year: {year}"}
    return response


@app.get('/a/{author_front_id}/network')
async def get_author(author_front_id: str, co_id: str = None):
    response = {'key': f"all of {author_front_id}'s collaborators"}
    if co_id:
        response = {
            'key': f"all of {author_front_id}'s papers with collaborator: {co_id}"}
    return response


@app.get('/a/{author_front_id}/keywords')
async def get_author(author_front_id: str, tag: str = None):
    response = {'key': f"all of {author_front_id}'s keywords"}
    if tag:
        response = {
            'key': f"all of {author_front_id}'s papers with keyword: {tag}"}
    return response


@app.get('/a/{author_front_id}/journals')
async def get_author(author_front_id: str, rank: str = None):
    response = {'key': f"all of {author_front_id}'s journal Qs"}
    if rank:
        response = {
            'key': f"all of {author_front_id}'s papers in {rank} journals"}
    return response
