SHELL := /bin/bash

# Prefer activated env python for stable --reload logs (same as project2).
# Keep conda-run variants as fallbacks.
PYTHON := python
UVICORN := python -m uvicorn

PYTHON_CONDA := conda run -n py310 python
UVICORN_CONDA := conda run -n py310 python -m uvicorn

PORT ?= 8003
APP ?= app.main:app
BASE_URL ?= http://127.0.0.1:$(PORT)

.PHONY: run run-conda health acceptance ps kill

run:
	$(UVICORN) $(APP) --reload --host 127.0.0.1 --port $(PORT)

run-conda:
	$(UVICORN_CONDA) $(APP) --reload --host 127.0.0.1 --port $(PORT)

health:
	@curl -s $(BASE_URL)/health && echo

acceptance:
	$(PYTHON) scripts/acceptance_ingest_recent.py --base-url $(BASE_URL)
	$(PYTHON) scripts/acceptance.py --base-url $(BASE_URL)

ps:
	@lsof -nP -iTCP:$(PORT) -sTCP:LISTEN || true

kill:
	@PIDS="$$(lsof -t -iTCP:$(PORT) -sTCP:LISTEN)"; \
	if [ -z "$$PIDS" ]; then echo "[OK] no process on :$(PORT)"; exit 0; fi; \
	echo "[INFO] stopping: $$PIDS"; \
	kill $$PIDS 2>/dev/null || true; \
	sleep 0.3; \
	PIDS2="$$(lsof -t -iTCP:$(PORT) -sTCP:LISTEN)"; \
	if [ -n "$$PIDS2" ]; then echo "[WARN] still alive, force killing: $$PIDS2"; kill -9 $$PIDS2 2>/dev/null || true; fi