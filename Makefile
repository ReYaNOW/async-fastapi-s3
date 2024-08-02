dev:
	RELOAD=True HOST='127.0.0.1' poetry run python3 s3_api/main.py

compose-dev:
	docker compose up -d --remove-orphans
	make dev

compose-start:
	docker compose --profile full up --remove-orphans

docker-run:
	docker run -p 8090:8090 --env-file .env reyanpy/async-fastapi-s3:latest

lint:
	poetry run ruff check

lint-fix:
	poetry run ruff check --fix

format:
	poetry run ruff format

test:
	docker compose -f docker-compose-test.yml up -d --remove-orphans
	trap 'docker compose -f docker-compose-test.yml stop' EXIT && poetry run pytest -vv -s
