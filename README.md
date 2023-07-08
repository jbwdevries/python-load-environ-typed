# load-environ-typed

This library lets you declare a NamedTuple or dataclass with
field types, and gives you a function that will `load` the
values from the environment, validating your types for you.

## Getting started

```python
from load_environ_typed import load

from dataclasses import dataclass

@dataclass
class MyEnviron:
	DB_HOST: str
	DB_PORT: int

environ = load(MyEnviron)
```

## Contributing

Check out this repo, and then use the following steps to test it:

```sh
python3 -m venv venv
venv/bin/pip install -r requirements-dev.txt
make test
```

## Deploying

```sh
venv/bin/python -m build
venv/bin/python -m twine upload dist/*
```
