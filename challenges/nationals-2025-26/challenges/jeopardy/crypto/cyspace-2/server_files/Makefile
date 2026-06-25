VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --quiet sympy

posts: $(VENV)/bin/activate
	$(PYTHON) generate_posts.py

run:
	docker compose up --build

stop:
	docker compose down

clean-venv:
	rm -rf $(VENV)

.PHONY: posts run stop clean-venv
