PYTHON := venv/bin/python3

test: py-typecheck py-unittest py-sast py-lint

py-typecheck:
	$(PYTHON) -m mypy --strict load_environ_typed tests

py-unittest:
	$(PYTHON) -m coverage run -m unittest tests/test_*.py
	$(PYTHON) -m coverage html

py-sast:
	$(PYTHON) -m pyflakes load_environ_typed tests

py-lint:
	$(PYTHON) -m pycodestyle --ignore=E721,W503 load_environ_typed tests

README.html: README.md
	pandoc -f markdown -s --highlight-style pygments --metadata title="load-environ-typed README" $^ -o $@
