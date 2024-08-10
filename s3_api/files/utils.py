import uuid

from fastapi import HTTPException, UploadFile


def get_unique_filename(filename: str):
    return f'{uuid.uuid4()}_{filename}'


def validate_img(image: UploadFile):
    if not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=415,
            detail='Only images are allowed for compression',
        )
