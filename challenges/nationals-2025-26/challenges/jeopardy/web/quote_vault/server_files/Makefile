.PHONY: build up down logs shell solve clean

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec ocr-rotator bash

solve:
	python3 tools/solve.py

clean:
	docker compose down -v
	docker rmi ocr-rotator:latest 2>/dev/null || true
