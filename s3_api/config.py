from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings, extra='allow'):
    host: str = '0.0.0.0'
    fastapi_s3_port: int
    reload: bool = False
    workers: int = 1

    s3_server_endpoint: str
    s3_access_key: str
    s3_secret_access_key: str
    use_ssl: bool = False
    default_bucket_name: str = 'my-bucket'

    main_server_url: HttpUrl

    model_config = SettingsConfigDict(env_file='.env')


config = Config()
