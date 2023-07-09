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
	db_host: str
	db_port: int

environ = load(MyEnviron)
```

## FAQ

### What types can I use? What about custom types?

By default, any type that takes a single string in it's constructor can be used
as type. Think of `int`, `str`, `float`, `pathlib.Path`, etc.

We've added default loaders for the types below:

- `bool` - "true" or "false", case insenstive
- `datetime.date` - Using `datetime.date.fromisoformat`
- `datetime.time` - Using `datetime.time.fromisoformat`
- `datetime.datetime` - Using `datetime.datetime.fromisoformat`

### How are fields matched to enviroment variables?

The loader assumes the names are the same, except that the class fields
are lowercase, and the environment fields are uppercase. If you have
different or more complicated rules, you can pass a name conversion
function via `field_name_to_var_name`.

```python
@dataclass
class MyEnviron:
    iso_date: datetime.date

environ = sut.load(MyEnviron, environ={
    'ISO_DATE': '2021-01-01',
})
```

### Can values be optional?

Certainly:

```python
@dataclass
class MyEnviron:
	DB_HOST: Optional[str]
```

However:

- empty string and "none" (case insensitive) count as `None`
- defaults take precedence over optionality

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
    # or, if you want ALL `date`s to use this loader:
    datetime.date: datetime.date.fromisoformat,
})
```

NOTE: date has a default loader, so you don't need to do this for `date`.

### Can I use Unions?

You can, but you need to use a default loader, as you need some
way to distinguish between the types, and there is no general
way to do so, at least not without enforcing our way of working on you.

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

For most types, you can simply set the default value as you're used to
with dataclasses. However, you may not want to instantiate an (expensive)
property as default. In those cases, you can pass defaults along using
the `defaults` argument.

```python
@dataclass
class MyEnviron:
	VAR: SomeExpensiveClass

environ = load(MyEnviron, defaults={
	'VAR': '#!serialized.data!#',
})
```

*NOTE*: `kw_only` requires Python3.10 or higher. Below 3.10, you can use
the `defaults` argument or order your variables. Similarly, if you plan
on solely using the `defaults` argument, you don't need `kw_only`.

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

First, update pyproject.toml with the new version number, and commit that.

Then:

```sh
rm -f dist/* # Clean old build files
venv/bin/python -m build
venv/bin/python -m twine upload dist/*
```
