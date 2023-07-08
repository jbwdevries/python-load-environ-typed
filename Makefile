test: py-typecheck py-unittest py-sast py-lint

py-typecheck:
	venv/bin/mypy --strict load_environ_typed test.py

py-unittest:
	venv/bin/python3 test.py

py-sast:
	venv/bin/pyflakes load_environ_typed test.py

py-lint:
	venv/bin/pycodestyle load_environ_typed test.py
