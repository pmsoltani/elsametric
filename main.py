import uvicorn
from fastapi import FastAPI

from api_queries import authors_list_frontend, get_author, get_author_papers, \
    get_author_trend, get_author_keywords, get_author_journals, \
    get_author_network, get_joint_papers_id

app = FastAPI()


@app.get('/')
async def home():
    return {'key': 'Visit list', 'url': 'http://127.0.0.1:8000/a/list'}


@app.get('/a/list')
async def show_authors_list():
    return authors_list_frontend


@app.get('/a/{id_frontend}')
async def show_author(id_frontend: str):
    response = get_author(id_frontend)
    return response


@app.get('/a/{id_frontend}/papers')
async def show_author(id_frontend: str, year: int = None, coID: str = None,
                      tag: str = None, q: str = None):
    response = get_author_papers(id_frontend)
    return response


@app.get('/a/{id_frontend}/trend')
async def show_author(id_frontend: str, year: int = None):
    response = get_author_trend(id_frontend)
    if year:
        response = get_author_papers(id_frontend, year)
    return response


@app.get('/a/{id_frontend}/network')
async def show_author(id_frontend: str, coID: str = None):
    response = get_author_network(id_frontend)
    if coID:
        response = get_joint_papers_id(id_frontend=id_frontend, co_id=coID)
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


if __name__ == "__main__":
    uvicorn.run(f'{__name__}:app', host='0.0.0.0', port=8000, reload=True)
