VENV     := .venv
PYTHON   := $(VENV)/bin/python
PIP      := $(VENV)/bin/pip

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --quiet pycryptodome

keys: $(VENV)/bin/activate
	$(PYTHON) generate_keys.py

run:
	docker compose up --build

stop:
	docker compose down

clean-venv:
	rm -rf $(VENV)

.PHONY: keys run stop clean-venv
