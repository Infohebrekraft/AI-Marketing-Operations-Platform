from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .config import get_settings
from .routes import auth_routes, org_routes, content_routes, linkedin_routes

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version='3.0.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth_routes.router)
app.include_router(org_routes.router)
app.include_router(content_routes.router)
app.include_router(linkedin_routes.router)


@app.get('/')
def root():
    return {'app': settings.app_name, 'version': '3.0.0', 'status': 'running'}


@app.get('/health')
def health():
    return {'status': 'ok'}
