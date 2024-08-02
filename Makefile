dev:
	poetry run fastapi dev s3_api/main.py

compose-dev:
	docker compose up -d --remove-orphans
	make dev

compose-start:
	docker compose --profile full up --remove-orphans

lint:
	poetry run ruff check

lint-fix:
	poetry run ruff check --fix

format:
	poetry run ruff format

test:
	docker compose -f docker-compose-test.yml up -d --remove-orphans
	trap 'docker compose -f docker-compose-test.yml stop' EXIT && poetry run pytest -vv -s
