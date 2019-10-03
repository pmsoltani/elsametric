import uvicorn
from fastapi import FastAPI

from api_queries import \
    initial_response, \
    authors_tuple_frontend, \
    get_author, \
    get_author_papers, \
    get_author_papers_year, \
    get_author_papers_keyword, \
    get_author_papers_q, \
    get_author_papers_co_id, \
    get_author_trend, \
    get_author_keywords, \
    get_author_qs, \
    get_author_network


app = FastAPI()


@app.get('/')
async def home():
    return initial_response


@app.get('/a')
async def home():
    return initial_response


@app.get('/a/list')
async def show_authors_list():
    return authors_tuple_frontend


@app.get('/a/{id_frontend}')
async def show_author(id_frontend: str):
    return get_author(id_frontend)


@app.get('/a/{id_frontend}/papers')
async def show_author(id_frontend: str, year: int = None, keyword: str = None,
                      q: str = None, coID: str = None,):
    params_set = {year, keyword, q, coID}
    if len(params_set) > 2:  # more than 1 parameter in the request
        return initial_response
    if year:
        return get_author_papers_year(id_frontend, year=year)
    if keyword:
        return get_author_papers_keyword(id_frontend, keyword=keyword)
    if q:
        return get_author_papers_q(id_frontend, q=q)
    if coID:
        return get_author_papers_co_id(id_frontend, co_id=coID)
    return get_author_papers(id_frontend)


@app.get('/a/{id_frontend}/trend')
async def show_author(id_frontend: str):
    return get_author_trend(id_frontend)


@app.get('/a/{id_frontend}/keywords')
async def show_author(id_frontend: str):
    return get_author_keywords(id_frontend)


@app.get('/a/{id_frontend}/qs')
async def show_author(id_frontend: str):
    return get_author_qs(id_frontend)


@app.get('/a/{id_frontend}/network')
async def show_author(id_frontend: str):
    return get_author_network(id_frontend)


if __name__ == "__main__":
    uvicorn.run(f'{__name__}:app', host='0.0.0.0', port=8000, reload=True)
