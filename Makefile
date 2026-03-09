SHELL := /bin/bash
PYTHON := conda run -n py310 python
UVICORN := conda run -n py310 python -m uvicorn

PORT ?= 8003
APP ?= app.main:app
BASE_URL ?= http://127.0.0.1:$(PORT)

.PHONY: dev health acceptance

dev:
	$(UVICORN) $(APP) --host 127.0.0.1 --port $(PORT) --reload

health:
	curl -s $(BASE_URL)/health

acceptance:
	$(PYTHON) scripts/acceptance.py --base-url $(BASE_URL)