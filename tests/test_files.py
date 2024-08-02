import io

import pytest
from PIL import Image, ImageChops
from botocore.exceptions import ClientError

from conftest import client, image, IMG_PATH, IMG_NAME, get_s3_client
from s3_api.config import config


async def test_upload_file():
    response = client.post(
        '/files',
        data={
            'new_filename': 'renamed_img_for_test.jpg',
            'set_unique_name': True,
        },
        files={'file': image},
    )

    assert response.status_code == 201
    uploaded_file_name = response.json()['filename']
    assert (
        uploaded_file_name.split('_', maxsplit=1)[1]
        == 'renamed_img_for_test.jpg'
    )

    try:
        async with get_s3_client() as s3_client:
            await s3_client.head_object(
                Bucket=config.default_bucket_name, Key=uploaded_file_name
            )
    except s3_client.exceptions.NoSuchKey:
        AssertionError('File was not uploaded')

    orig_img = Image.open(f'{IMG_PATH}{IMG_NAME}')

    async with get_s3_client() as s3_client:
        response = await s3_client.get_object(
            Bucket=config.default_bucket_name, Key=uploaded_file_name
        )
        async with response['Body'] as stream:
            downloaded_image = await stream.read()
            img_from_response = Image.open(io.BytesIO(downloaded_image))

    diff = ImageChops.difference(orig_img, img_from_response)

    assert (
        diff.getbbox() is None
    ), 'Uploaded image is not the same as original image'


def test_negative_upload_file():
    response = client.post(
        '/files',
        data={
            'new_filename': 'renamed_img_for_test.jpg',
            'set_unique_name': True,
        },
    )

    assert (
        response.status_code == 422
    ), 'No HTTP 422 when trying to upload file without file itself'


async def test_download_file(upload_file):
    response = client.get(f'/files/{IMG_NAME}')
    assert response.status_code == 200

    orig_img = Image.open(f'{IMG_PATH}{IMG_NAME}')
    img_from_response = Image.open(io.BytesIO(response.read()))

    diff = ImageChops.difference(orig_img, img_from_response)

    assert (
        diff.getbbox() is None
    ), 'Downloaded image is not the same as original image'


async def test_negative_download_file(upload_file):
    response = client.get(f'/files/something.jpg')
    assert response.status_code == 404


async def test_delete_file(upload_file):
    response = client.delete(f'/files/{IMG_NAME}')
    assert response.status_code == 200
    assert response.json() == {
        'details': f'Deleted file if it existed: {IMG_NAME}'
    }

    async with get_s3_client() as s3_client:
        with pytest.raises(ClientError):
            await s3_client.head_object(
                Bucket=config.default_bucket_name, Key=IMG_NAME
            )
            pytest.fail('Image was not deleted')


async def test_negative_delete_file(upload_file):
    response = client.delete(f'/files/something.jpg')
    assert response.status_code == 200


async def test_find_files():
    for n in range(2):
        client.post(
            '/files',
            data={'new_filename': f'{n}other_filename.jpg'},
            files={'file': ('image.jpg', image, 'image/jpeg')},
        )
    client.post(
        '/files',
        data={'new_filename': f'different_name.jpg'},
        files={'file': image},
    )
    response = client.get(f'/files', params={'pattern': 'other_filename.jpg'})
    assert response.status_code == 200
    assert response.json() == {
        'files': [
            {
                'file_name': '0other_filename.jpg',
                'content_type': 'image/jpeg',
            },
            {
                'file_name': '1other_filename.jpg',
                'content_type': 'image/jpeg',
            },
        ]
    }
