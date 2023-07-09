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

## FAQ

### What types can I use? What about custom types?

By default, any type that takes a single string in it's constructor can be used
as type. Think of `int`, `str`, `float`, `pathlib.Path`, etc.

We've added default loaders for the types below:

- `bool` - "true", "FalSe"
- `datetime.date` - Using `datetime.date.fromisoformat`
- `datetime.time` - Using `datetime.time.fromisoformat`
- `datetime.datetime` - Using `datetime.datetime.fromisoformat`

### Can values be optional?

Certainly:

```python
@dataclass
class MyEnviron:
	DB_HOST: Optional[str]
```

However:

- empty string and "none" count as `None`
- defaults take precedence over optionality
- this does not work for dataclass properties

### Can I use Unions?

You can, but you need to use a default loader, as you need some
way to distinguish between the types, and there is no general
way to do so, at least not without enforcing our way of working on you.

### What if my type cannot take a string in its constructor?

You can pass so-called loader functions. These take in a string, and are
expected to return a value of the given type, or raise a `ValueError` when
the given string is not valid for the given type. This is also the
mechanism that we use to support standard Python types such `datetime.date`,
which is shown below.

```python
@dataclass
class MyEnviron:
    ISO_DATE: datetime.date

environ = sut.load(MyEnviron, environ={
    'ISO_DATE': '2021-01-01',
}, loaders={
    'ISO_DATE': datetime.date.fromisoformat,
})

self.assertEqual(datetime.date(2021, 1, 1), environ.ISO_DATE)
```

NOTE: date has a default loader, so you don't need to do this for `date`.

### How do I work with default values?

If you want default values, it's probably best to have use a dataclass
with `kw_only=True`, as otherwise you have to order your variables based
on whether there's a default or not.

```python
@dataclass(kw_only=True)
class MyEnviron:
	DB_HOST: str
	DB_PORT: int = 3306
```

NOTE: `kw_only` requires Python3.10 or higher

For most types, you can simply set the default value as you're used to
with dataclasses. However, you may not want to instantiate an (expensive)
property as default. In those cases, you can pass defaults along using
the `defaults` argument.

```python
@dataclass(kw_only=True)
class MyEnviron:
	VAR: SomeExpensiveClass

environ = load(MyEnviron, defaults={
	'VAR': '#!serialized.data!#',
})
```

### Load returns an instance. What if I want a global?

Since `environ` is available at startup, and doesn't change, it's perfectly
valid to just instantiate a global variable. You should probably use a
frozen dataclass for this.

```python
@dataclass(frozen=True)
class MyEnviron:
	DB_HOST: str
	DB_PORT: int

ENVIRON = load(MyEnviron)
```

### What if there's an issue with the default loaders?

First, the loaders you pass will be taken before using the default loaders.

Second, if you have more structural issues with the default loaders, simply
pass `use_default_loaders=False`.

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
