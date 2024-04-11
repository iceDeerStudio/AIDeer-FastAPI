from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import config
from app.core.managers.static import StaticFilesManager

from app.core.log import log

app = FastAPI(
    title=config.project_name, openapi_url=f"{config.api_prefix}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=config.api_prefix)

StaticFilesManager.init_static_files(app)

log.init_config()
