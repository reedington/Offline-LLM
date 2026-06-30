.PHONY: test benchmark run

test:
	python -m compileall app
	python -m pytest ../tests -q

benchmark:
	python -m app.benchmark

run:
	uvicorn main:app --host 127.0.0.1 --port 8000
