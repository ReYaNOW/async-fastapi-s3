from fastapi import APIRouter, Depends, UploadFile, status, Body
from fastapi.responses import StreamingResponse

from s3_api.files.dependencies import (
    get_s3_client,
)
from s3_api.files.schemas import (
    UploadResponse,
    UploadUniqueFileNameResponse,
    ListRequest,
    ListResponse,
)
from s3_api.files.service import (
    get_unique_filename,
    S3Client,
)

router = APIRouter(prefix='/files', tags=['Files'])


@router.get('/{filename}')
async def download(
    filename: str,
    client: S3Client = Depends(get_s3_client),
):
    stream = client.yield_media_type_then_stream_file(filename)
    media_type = await anext(stream)
    response = StreamingResponse(stream, media_type=media_type)

    if 'image' not in media_type:
        response.headers[
            'Content-Disposition'
        ] = f'attachment; filename={filename}'

    return response


@router.post('', status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile,
    new_filename: str = Body(''),
    set_unique_name: bool = Body(False),
    client: S3Client = Depends(get_s3_client),
) -> UploadResponse | UploadUniqueFileNameResponse:
    filename = new_filename if new_filename else file.filename

    if set_unique_name:
        filename = get_unique_filename(filename)
    await client.upload_file(file, filename)

    if set_unique_name:
        return UploadUniqueFileNameResponse(filename=filename)
    return UploadResponse(filename=filename)


@router.delete('/{filename}')
async def delete(
    filename: str,
    client: S3Client = Depends(get_s3_client),
):
    await client.remove_file(filename)

    return {'details': f'Deleted file if it existed: {filename}'}


@router.get('', response_model=ListResponse)
async def find(
    params: ListRequest = Depends(), client: S3Client = Depends(get_s3_client)
):
    return await client.find_files(params.pattern)
