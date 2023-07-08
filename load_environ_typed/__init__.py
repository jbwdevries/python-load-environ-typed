from typing import Any, Callable, List, Mapping, Optional, Type, TypeVar

import dataclasses
import os

T = TypeVar('T')


class LoadEnvironmentException(BaseException):
    pass


def load(
    type_: Type[T],
    *,
    environ: Optional[Mapping[str, str]] = None,
    defaults: Optional[Mapping[str, str]] = None,
    loaders: Optional[Mapping[str, Callable[[str], Any]]] = None,
) -> T:
    """
    Loads the data from environ into the given class

    If environ is none, use os.environ
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

    args: List[Any] = []

    errors: List[str] = []

    for field_name in field_name_list:
        field_type = type_.__annotations__[field_name]
        field_loader = loaders.get(field_name, field_type)

        try:
            field_value_str = environ[field_name]
        except KeyError:
            try:
                field_value_str = defaults[field_name]
            except KeyError:
                try:
                    field_value = typed_defaults[field_name]
                    args.append(field_value)
                except KeyError:
                    errors.append(
                        'No value in environ for required property'
                        f' {field_name} of type '
                        f'{field_type.__module__}.{field_type.__name__}')
                continue

        field_loader = getattr(
            field_loader, 'load_environ_typed', field_loader)

        try:
            field_value = field_loader(field_value_str)
        except ValueError as ex:
            errors.append(
                'ValueError for property'
                f' {field_name} of type '
                f'{field_type.__module__}.{field_type.__name__}: {str(ex)}'
            )
            continue

        args.append(field_value)

    if errors:
        raise LoadEnvironmentException(errors)

    return type_(*args)
