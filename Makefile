.PHONY: install run test lint typecheck check docker

install:
	python -m pip install -e '.[dev]'

run:
	uvicorn resume_agent.api:app --reload

test:
	pytest --cov=resume_agent --cov-report=term-missing

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy src

check: lint typecheck test

docker:
	docker compose up --build

