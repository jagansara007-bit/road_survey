# Makefile for Road Damage System

.PHONY: help setup check lint test run-ai clean

help:
	@echo "Available commands:"
	@echo "  make setup    - Install dependencies into virtualenv via uv"
	@echo "  make check    - Run linting (ruff) and test suite (pytest)"
	@echo "  make lint     - Run ruff linter"
	@echo "  make test     - Run pytest unit tests"
	@echo "  make run-ai   - Start FastAPI microservice on localhost:8000"

setup:
	uv sync --extra dev

lint:
	uv run ruff check .

test:
	uv run pytest

check: lint test

run-ai:
	uv run --directory ai-service python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
