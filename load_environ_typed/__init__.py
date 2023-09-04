from typing import (
    Any, Callable, Dict, List, Mapping, Optional,
    Tuple, Type, TypeVar, Union,
    get_type_hints,
)

try:
    from types import UnionType  # type: ignore [attr-defined,unused-ignore]
except ImportError:
    class UnionType:  # type: ignore[no-redef]
        """
        Have some kind of class so the isinstance check works
        for python versions below 3.10
        """

import dataclasses
import datetime
import os

T = TypeVar('T')


class LoadEnvironmentException(BaseException):
    pass


def load_bool(raw: str) -> bool:
    if 'true' == raw.lower():
        return True

    if 'false' == raw.lower():
        return False

    raise ValueError(f'"{raw}" cannot be parsed as boolean')


DEFAULT_LOADERS = {
    bool: load_bool,
    datetime.date: datetime.date.fromisoformat,
    datetime.time: datetime.time.fromisoformat,
    datetime.datetime: datetime.datetime.fromisoformat,
}


LoaderMap = Mapping[Union[str, Type[Any]], Callable[[str], Any]]
NameConverter = Callable[[str], str]


def load(
    type_: Type[T],
    *,
    environ: Optional[Mapping[str, str]] = None,
    defaults: Optional[Mapping[str, str]] = None,
    loaders: Optional[LoaderMap] = None,
    use_default_loaders: bool = True,
    field_name_to_var_name: NameConverter = lambda x: x.upper(),
) -> T:
    """
    Loads the data from environ into the given class

    If environ is none, use os.environ.

    If a key is not in `environ`, check `defaults`, and if it's
    not there, check the defaults on the type. Defaults is
    expected to use the environment variable names, not the class
    field names.

    `loaders` are functions that take in a string from environ,
    and return a class of the right type. There are a bunch of
    default loaders (see DEFAULT_LOADERS) - you can disable these
    via `use_default_loaders=False`.

    The name of the class fields is also used as the environment
    variable. However, Python uses lowercase by default, where
    environment variables are uppercase by default, so we convert
    lowercase into uppercase. If you have different rules or more
    complicated rules, pass a function via `field_name_to_var_name`.
    """
    if environ is None:
        environ = dict(os.environ)
    if defaults is None:
        defaults = {}
    if loaders is None:
        loaders = {}

    if dataclasses.is_dataclass(type_):
        dc_field_list = dataclasses.fields(type_)
        field_name_list = [x.name for x in dc_field_list]
        typed_defaults = {
            x.name: x.default
            for x in dc_field_list
            if x.default is not dataclasses.MISSING
        }
    else:
        try:
            field_name_list = getattr(type_, '_fields')
            typed_defaults = getattr(type_, '_field_defaults')
        except AttributeError:
            raise RuntimeError(
                f'{type_!r} is not a dataclasses.dataclass'
                ' and not a typing.NamedTuple')

    kwargs: Dict[str, Any] = {}

    errors: List[str] = []

    # Load the type annotations in case they are forward references
    annotations = get_type_hints(type_)

    for field_name in field_name_list:
        variable_name = field_name_to_var_name(field_name)

        field_type = annotations[field_name]
        field_type, is_optional_type = check_optional(field_type)

        try:
            field_loader = loaders[field_name]
        except KeyError:
            try:
                if not use_default_loaders:
                    raise KeyError

                field_loader = DEFAULT_LOADERS[field_type]
            except KeyError:
                field_loader = field_type

        try:
            field_value_str = environ[variable_name]
        except KeyError:
            try:
                field_value_str = defaults[variable_name]
            except KeyError:
                try:
                    field_value = typed_defaults[field_name]
                    kwargs[field_name] = field_value
                except KeyError:
                    if is_optional_type:
                        kwargs[field_name] = None
                    else:
                        errors.append(
                            'No value in environ for required field'
                            f' {variable_name} of type '
                            f'{field_type.__module__}.{field_type.__name__}')
                continue

        if is_optional_type and is_optional_value(field_value_str):
            kwargs[field_name] = None
            continue

        field_loader = getattr(
            field_loader, 'load_environ_typed', field_loader)

        try:
            field_value = field_loader(field_value_str)
        except ValueError as ex:
            errors.append(
                'ValueError for field'
                f' {variable_name} of type '
                f'{field_type.__module__}.{field_type.__name__}: {str(ex)}'
            )
            continue

        kwargs[field_name] = field_value

    if errors:
        raise LoadEnvironmentException(errors)

    return type_(**kwargs)


def check_optional(type_: Type[Any]) -> Tuple[Type[Any], bool]:
    """
    Checks whether the given type is an Optional variant

    This has some wonkyness regarding which Python version we're on
    """
    if getattr(type_, '__origin__', None) is Optional:
        raise NotImplementedError('TODO')

    if (getattr(type_, '__origin__', None) is Union
            or isinstance(type_, UnionType)):
        args = tuple(
            x
            for x in type_.__args__
            if x is not None and x != type(None)
        )

        if len(args) == len(type_.__args__):
            return type_, False

        if len(args) == 1:
            return args[0], True

        # Union types need a custom loader anyhow
        return type_, False

    return type_, False


def is_optional_value(raw: str) -> bool:
    return raw == '' or raw.lower() == 'none'
