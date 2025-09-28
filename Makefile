.PHONY: dev test web
dev:
	python -m uvicorn src.huntlens.api:app --reload
test:
	pytest -q
web:
	cd web && npm run dev
