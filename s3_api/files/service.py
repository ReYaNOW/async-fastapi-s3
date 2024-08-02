import uuid
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

    def info_message(self, msg):
        info_logger.info(msg)

    def error_message(self, msg):
        error_logger.error(msg)

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client('s3', **self.config) as client:
            yield client

    async def yield_media_type_then_stream_file(self, filename: str):
        try:
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

        except client.exceptions.NoSuchKey:
            raise HTTPException(
                status_code=404,
                detail=f'File not found: {filename}',
            ) from None

        except ClientError as e:
            self.error_message(f'Error downloading file: {filename}\n{e}')

    async def upload_file(
        self,
        file: UploadFile,
        filename,
    ):
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
                self.info_message(f'File {filename} successfully uploaded')
            # This is crucial to catch any error to abort upload
            except Exception as e:
                print(e)
                self.error_message(f'Error uploading file: {filename}\n{e}')
                await client.abort_multipart_upload(
                    Bucket=config.default_bucket_name,
                    Key=filename,
                    UploadId=upload_id,
                )
                raise HTTPException(status_code=500, detail=str(e)) from e

    async def remove_file(self, filename: str):
        try:
            async with self.get_client() as client:
                await client.delete_object(
                    Bucket=self.bucket_name, Key=filename
                )
                self.info_message(
                    f'File {filename} successfully deleted if it existed'
                )

        except ClientError as e:
            self.error_message(f'Error removing file: {filename}\n{e}')
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def find_files(self, pattern: str):
        try:
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

        except ClientError as e:
            self.info_message(
                f'There was some error while trying to filter '
                f'files with pattern: {pattern}\n{e}'
            )
            raise HTTPException(status_code=500, detail=str(e)) from e

    async def create_default_bucket(self):
        async with self.get_client() as client:
            try:
                await client.create_bucket(Bucket=config.default_bucket_name)
                self.info_message(
                    f'Successfully create default bucket '
                    f'with name {config.default_bucket_name}'
                )

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code != 'BucketAlreadyOwnedByYou':
                    raise e


def get_unique_filename(filename: str):
    return f'{uuid.uuid4()}_{filename}'
