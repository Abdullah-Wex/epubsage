# Makefile for EpubSage

.PHONY: install format test lint clean

install:
	uv sync

format:
	uv run autopep8 --in-place --recursive --aggressive --aggressive .
	uv run ruff check --fix .

test:
	uv run pytest

lint:
	uv run ruff check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .uv
