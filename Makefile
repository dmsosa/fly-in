install:
	poetry install

install-req:
	python3 -m venv myvenv
	source ./myvenv/bin/activate
	pip install -r requirements.txt
	echo "Ready to run"

run: install
	python3 main.py

lint:
	python3 -m flake8 .
	python3 -m mypy .

lint-strict: lint
	python3 -m mypy --strict .
