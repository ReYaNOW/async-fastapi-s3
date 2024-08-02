from uuid import UUID

from pydantic import BaseModel
from pydantic import field_validator


class ListRequest(BaseModel):
    pattern: str = ''


class File(BaseModel):
    file_name: str
    content_type: str


class ListResponse(BaseModel):
    files: list[File] = []


class UploadResponse(BaseModel):
    filename: str


class UploadUniqueFileNameResponse(BaseModel):
    filename: str

    @field_validator('filename')
    def validate_unique_filename(cls, value):
        try:
            uuid, filename = value.split('_', 1)
            UUID(uuid, version=4)
        except ValueError:
            raise ValueError(
                f"Incorrect filename format. Filename: {value}\n"
                "Should be 'UUID4_filename'"
            )
        return value
