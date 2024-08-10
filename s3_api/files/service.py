import functools
import inspect
from contextlib import asynccontextmanager

import aiohttp
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from s3_api.config import config
from s3_api.utils import error_logger, info_logger

UPLOAD_CHUNK_SIZE = 5 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


class S3Client:
    def __init__(self):
        self.config = {
            'aws_access_key_id': config.s3_access_key,
            'aws_secret_access_key': config.s3_secret_access_key,
            'endpoint_url': config.s3_server_endpoint,
            'use_ssl': config.use_ssl,
        }
        self.bucket_name = config.default_bucket_name
        self.session = get_session()
        self.error_message = ''
        self.success_message = ''

    def log_success_message(self):
        info_logger.info(self.success_message)

    def log_error_message(self, e):
        error_logger.error(f'{self.error_message}\n{e}')

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client('s3', **self.config) as client:
            yield client

    def display_exception(self, e, args, kwargs):
        error_code = e.response['Error']['Code']
        filename = kwargs.get('filename', args[0] if args else None)

        match error_code:
            case 'NoSuchKey' if isinstance(filename, str):
                raise HTTPException(
                    status_code=404,
                    detail=f'File not found: {filename}',
                ) from None

            case 'BucketAlreadyOwnedByYou':
                pass

            case _:
                self.log_error_message(e)
                raise HTTPException(status_code=500, detail=str(e)) from e

    @staticmethod
    def error_handler(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            async def generator_wrapper(self, *args, **kwargs):
                try:
                    async for value in func(self, *args, **kwargs):
                        yield value
                except ClientError as e:
                    self.display_exception(e, args, kwargs)

            try:
                if inspect.isasyncgenfunction(func):
                    return generator_wrapper(self, *args, **kwargs)
                result = await func(self, *args, **kwargs)
                self.log_success_message()
                return result
            except ClientError as e:
                self.display_exception(e, args, kwargs)

        return wrapper

    @error_handler
    async def yield_media_type_then_stream_file(self, filename: str):
        self.success_message = f'Successfully downloaded file: {filename}'
        self.error_message = f'Error downloading file: {filename}'

        async with self.get_client() as client:
            resp = await client.get_object(
                Bucket=config.default_bucket_name, Key=filename
            )
            content_type: str = resp['ResponseMetadata']['HTTPHeaders'][
                'content-type'
            ]
            yield content_type
            async with resp['Body'] as stream:
                stream: aiohttp.ClientResponse
                while True:
                    chunk = await stream.content.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    yield chunk

    @error_handler
    async def upload_file(
        self,
        filename,
        file: UploadFile,
    ):
        self.success_message = (
            f'Successfully uploaded file in chunks: {filename}'
        )
        self.error_message = f'Error uploading file in chunks: {filename}'

        async with self.get_client() as client:
            try:
                resp = await client.create_multipart_upload(
                    Bucket=config.default_bucket_name,
                    Key=filename,
                    ContentType=file.content_type,
                )
                upload_id = resp['UploadId']
                parts = []
                part_number = 1
                while True:
                    chunk = await file.read(UPLOAD_CHUNK_SIZE)
                    if not chunk:
                        break

                    part = await client.upload_part(
                        Body=chunk,
                        Bucket=config.default_bucket_name,
                        Key=filename,
                        UploadId=upload_id,
                        PartNumber=part_number,
                    )
                    parts.append(
                        {'ETag': part['ETag'], 'PartNumber': part_number}
                    )
                    part_number += 1
                await client.complete_multipart_upload(
                    Bucket=config.default_bucket_name,
                    Key=filename,
                    UploadId=upload_id,
                    MultipartUpload={'Parts': parts},
                )

            except ClientError as e:
                await client.abort_multipart_upload(
                    Bucket=config.default_bucket_name,
                    Key=filename,
                    UploadId=upload_id,
                )
                raise e

    @error_handler
    async def remove_file(self, filename: str):
        self.success_message = (
            f'Successfully removed file if it existed: {filename}'
        )
        self.error_message = f'Error removing file: {filename}'

        async with self.get_client() as client:
            await client.delete_object(Bucket=self.bucket_name, Key=filename)

    @error_handler
    async def find_files(self, pattern: str):
        self.success_message = (
            f'Successfully filtered files with pattern: "{pattern}"'
        )
        self.error_message = f'Error filtering files with pattern: {pattern}'

        async with self.get_client() as client:
            paginator = client.get_paginator('list_objects_v2')
            result = []
            async for page in paginator.paginate(Bucket=self.bucket_name):
                for obj in page.get('Contents', []):
                    if pattern in obj['Key']:
                        filename = obj['Key']
                        head_response = await client.head_object(
                            Bucket=self.bucket_name, Key=filename
                        )
                        content_type = head_response.get(
                            'ContentType', 'application/octet-stream'
                        )
                        result.append(
                            {
                                'file_name': filename,
                                'content_type': content_type,
                            }
                        )
        return {'files': result}

    @error_handler
    async def create_default_bucket(self):
        self.success_message = (
            f'Successfully created default bucket with name '
            f'{config.default_bucket_name}'
        )
        self.error_message = (
            f'Default bucket with name: '
            f'{config.default_bucket_name} already exists\nPrevent creating...'
        )

        async with self.get_client() as client:
            await client.create_bucket(Bucket=config.default_bucket_name)
