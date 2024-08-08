from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from s3_api.config import config
from s3_api.files.dependencies import get_s3_client
from s3_api.files.router import router as files_router


@asynccontextmanager
async def lifespan(_):
    client = get_s3_client()
    await client.create_default_bucket()
    yield


app = FastAPI(title='S3 Server API', lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.main_server_url],
    allow_methods=['GET', 'POST', 'DELETE'],
)

app.include_router(files_router)


if __name__ == '__main__':
    print(config.host)
    uvicorn.run(
        'main:app',
        host=config.host,
        port=config.port,
        reload=config.reload,
        workers=config.workers,
    )
