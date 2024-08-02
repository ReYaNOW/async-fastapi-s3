from contextlib import asynccontextmanager

import pytest
from aiobotocore.session import get_session
from fastapi.testclient import TestClient

from s3_api.config import config
from s3_api.main import app

IMG_PATH = 'tests/fixtures/images/'
IMG_NAME = 'img_for_test.jpg'

client = TestClient(app)


@asynccontextmanager
async def get_s3_client():
    params = {
        'aws_access_key_id': config.s3_access_key,
        'aws_secret_access_key': config.s3_secret_access_key,
        'endpoint_url': config.s3_server_endpoint,
        'use_ssl': config.use_ssl,
    }
    session = get_session()
    async with session.create_client('s3', **params) as client:
        yield client


with open(f'{IMG_PATH}{IMG_NAME}', 'rb') as file:
    image = file.read()


@pytest.fixture(scope='function')
def upload_file():
    client.post(
        '/files', files={'file': image}, data={'new_filename': IMG_NAME}
    )


@pytest.fixture(autouse=True, scope='session')
def create_default_bucket():
    # trigger lifespan from main.py
    with TestClient(app):
        pass


@pytest.fixture(autouse=True, scope='function')
async def clear_bucket():
    async with get_s3_client() as s3_client:
        paginator = s3_client.get_paginator('list_objects_v2')
        async for result in paginator.paginate(
            Bucket=config.default_bucket_name
        ):
            objects = result.get('Contents', [])
            if objects:
                delete_objects = [{'Key': obj['Key']} for obj in objects]

                await s3_client.delete_objects(
                    Bucket=config.default_bucket_name,
                    Delete={'Objects': delete_objects},
                )
