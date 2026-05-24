SHELL := /usr/bin/env bash
DB_NAME := backend_devops_interview

.PHONY: setup install db migrate seed run dev

setup: install db migrate seed
	@echo "✅ Proyecto listo. Ejecuta 'make run' para iniciar el servidor."

install:
	mise install
	uv sync

db:
	createdb $(DB_NAME)

migrate:
	uv run python manage.py migrate

seed:
	uv run python manage.py seed

run:
	uv run python manage.py runserver

