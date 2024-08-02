[![Linter check](https://github.com/ReYaNOW/async-fastapi-s3/actions/workflows/linter_check.yml/badge.svg)](https://github.com/ReYaNOW/async-fastapi-s3/actions/workflows/linter_check.yml)
[![Run tests](https://github.com/ReYaNOW/async-fastapi-s3/actions/workflows/run_tests.yml/badge.svg)](https://github.com/ReYaNOW/async-fastapi-s3/actions/workflows/run_tests.yml)
[![Docker push](https://github.com/ReYaNOW/async-fastapi-s3/actions/workflows/docker_push.yml/badge.svg)](https://github.com/ReYaNOW/async-fastapi-s3/actions/workflows/docker_push.yml)
[![Maintainability](https://api.codeclimate.com/v1/badges/d8f91faaed7521df13d2/maintainability)](https://codeclimate.com/github/ReYaNOW/async-fastapi-s3/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/d8f91faaed7521df13d2/test_coverage)](https://codeclimate.com/github/ReYaNOW/async-fastapi-s3/test_coverage)

## Asynchronous REST API to work with S3

This API provides routes to to work with files:
upload, download, delete, find by pattern.  

There are tests written using Pytest.   
Input data validation has been implemented.  
There is an [example](https://github.com/ReYaNOW/async-fastapi-s3/blob/main/docker-compose.yml)
of launching in Docker Compose in conjunction with [minIO](https://min.io/).  


Stack: Python3.11, FastApi, Asyncpg, Pytest, Docker

## Documentation
You can open swagger documentation at http://127.0.0.1:8090/docs after start  
You can also make requests to the web application there

![App preview](https://github.com/ReYaNOW/ReYaNOW/blob/main/Images/s3_preview.png?raw=true)

# Usage  
1. Clone the repository

```
git clone https://github.com/ReYaNOW/MemesAPI.git
```

2. Go to the project directory and rename .env.example to .env
  
```
cd MemesAPI
mv .env.example .env
```  
3. Specify MAIN_SERVER_URL in .env from witch you will make requests to this server.  
Other requests will be blocked via [CORS](https://developer.mozilla.org/ru/docs/Web/HTTP/CORS).  
Leave it as is if you are going to run it locally.  
  
[Optional] If you already have an S3 server, you can change variables in .env.    
Set USE_SSL to True if your server has a ssl certificate.  
```dotenv
S3_SERVER_ENDPOINT=http://127.0.0.1:9000
USE_SSL=False 

S3_ACCESS_KEY=root_user
S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCY
```  
- [How to include in a Docker Compose](#how-to-include-in-a-docker-compose-)
- [How to start a web application](#how-to-start-a-web-application-)
- [How to start a web application in Docker container](#How-to-start-a-web-application-in-Docker-container)
- [How to run tests](#How-to-run-tests)

## How to include in a Docker Compose  
To use this web app in a docker compose file include something like this  
```yaml
s3-api:
  image: reyanpy/async-fastapi-s3:latest
  container_name: s3-api
  env_file:
    - .env
  environment:
    S3_ACCESS_KEY: <your access key, BUT you should put it in .env>
    S3_SECRET_ACCESS_KEY: <your secret access key, BUT you should put it in .env>
    S3_SERVER_ENDPOINT: <Url to your server>
  ports:
    - 8090:8090
```

## How to start a web application  
This requires [Poetry](https://python-poetry.org/docs/#installing-with-pipx)  

4. Install Python dependencies
  
```
poetry install
```

5. Start a local server if you specified your S3 server
  
```
make dev
```

Либо сначала запустить сервер [MinIO](https://min.io/) в Docker контейнере, а потом уже сам сервер
  
```
make compose-dev
```

## How to start a web application in Docker container

4. Start a local server if you specified your S3 server in container
  
```
make docker-run
```

Or first run the [MinIO](https://min.io/) server in a Docker container,
then the server itself
  
```
make compose-start
```
  
## New features
If you are missing some interactions with S3,
create an issue and I will add it ASAP

## How to run tests
1. Install all python dependencies as described [here](#Usage-)

2. Run tests
  
```
make test
```
