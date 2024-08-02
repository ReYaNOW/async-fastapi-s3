from s3_api.files.service import S3Client


def get_s3_client() -> S3Client:
    return S3Client()
