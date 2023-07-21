from fastapi import FastAPI, Request, Response, status
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
import pickle

db_file_name = 'data/db.pickle'
class Router(BaseModel):
    name: str
    rule: str
    healthcheck_url: str = '/'
    healthcheck: bool = False,
    healthcheck_port: int = 80
    urls: list[str] = []

    def __iter__(self):
        for i in self.dict():
            yield i

    def __getitem__(self, item):
        return self.dict()[item]

    def __setitem__(self, key, value):
        self.dict()[key] = value

    def dict(self):
        return {
            'name': self.name,
            'rule': self.rule,
            'urls': self.urls,
            'healthcheck_url': self.healthcheck_url,
            'healthcheck': self.healthcheck,
            'healthcheck_port': self.healthcheck_port
        }

    def update_urls(self, urls: list[str]):
        for url in urls:
            if url not in self.urls:
                self.urls.append(url)

    def delete_urls(self, urls: list[str]):
        for url in urls:
            if url in self.urls:
                self.urls.remove(url)

class DB:
    def __init__(self):
        self.db = {}

    def __iter__(self):
        for i in self.db:
            yield i

    def __getitem__(self, name: str):
        return self.db[name]

    def add(self, item: Router):
        self.db[item.name] = item

    def delete(self, name: str):
        del self.db[name]

    def dump(self):
        return [i.dict() for i in self.db.values()]

    def save(self):
        with open(db_file_name, 'wb') as f:
            pickle.dump(self, f)


templates = Jinja2Templates(directory='templates')
try:
    with open(db_file_name, 'rb') as f:
        db = pickle.load(f)
except FileNotFoundError:
    db = DB()
    db.save()

api = FastAPI(
    title="traefik http provider api",
    openapi_url="/openapi.json",
)


@api.get('/routers')
async def list_all_routers():
    return iter(db)


@api.get('/routers/{name}')
async def get_router_details_by_name(name: str, response: Response):
    if name in iter(db):
        return db[name].dict()
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'message': 'failed, record not found'}


@api.get('/routers/{name}/urls')
async def get_router_urls(name: str, response: Response):
    if name in iter(db):
        return db[name]['urls']
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'message': 'failed, record not found'}


@api.put('/routers/{name}/urls')
async def update_router_urls(name: str, urls: list[str], response: Response):
    if name in iter(db):
        db[name].update_urls(urls)
        db.save()
        return {'message': 'success', 'data': db[name].dict()}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'message': 'failed, record not found'}


@api.delete('/routers/{name}/urls')
async def delete_router_urls(name: str, urls: list[str], response: Response):
    if name in iter(db):
        db[name].delete_urls(urls)
        if len(db[name]['urls']) == 0:
            db.delete(name)
        db.save()
        return {'message': 'success'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'message': 'failed, record not found'}


@api.delete('/routers/{name}')
async def delete_router(name: str, response: Response):
    if name in iter(db):
        db.delete(name)
        db.save()
        return {'message': 'success'}
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'message': 'failed, record not found'}


@api.post('/routers')
async def create_router(router: Router):
    if router.name not in iter(db):
        db.add(router)
        db.save()
        return {'message': 'success', 'data': router.dict()}
    else:
        db[router.name].update_urls(router.urls)
        db.save()
        return {'message': 'record already exists, updating urls', 'data': router.dict()}


@api.get('/')
async def index(request: Request):
    return templates.TemplateResponse('config.json',
                                      {'request': request, 'routers': db.dump()},
                                      media_type='application/json')

