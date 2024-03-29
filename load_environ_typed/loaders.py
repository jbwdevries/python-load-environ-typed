from typing import Dict, List, Optional, Union

import csv
from pathlib import Path

from load_environ_typed import load_bool
from load_environ_typed import _logfmt


def load_bool_or_int(raw: str) -> Union[bool, int]:
    """
    Return a boolean when raw is equal to TRUE or FALSE
    (case insenstive). Else, returns it an int.
    """
    try:
        return load_bool(raw)
    except ValueError:
        return int(raw)


def load_bool_or_str(raw: str) -> Union[bool, str]:
    """
    Return a boolean when raw is equal to TRUE or FALSE
    (case insenstive). Else, returns it as string.

    Empty string is also returned as string.
    """
    try:
        return load_bool(raw)
    except ValueError:
        return raw


def load_bool_or_path(raw: str) -> Union[bool, Path]:
    """
    Return a boolean when raw is equal to TRUE or FALSE
    (case insenstive). Else, returns it as path.

    Empty string is also returned as path.
    """
    try:
        return load_bool(raw)
    except ValueError:
        return Path(raw)


def load_list_int(raw: str) -> List[int]:
    """
    Returns a list of integers

    Configure this in the environment by using a comma
    separated list of integers. See load_list_str for
    more details.
    """
    lst = load_list_str(raw)

    return [int(x.strip()) for x in lst]


def load_list_str(raw: str) -> List[str]:
    """
    Returns a list of strings

    Configuring this in the environment means using CSV, with:
    - comma as delimiter
    - double quote as quote char
    - double quotes in your value have to be doubled again
    - we skip spaces after the comma
    """
    rdr = csv.reader(
        [raw],
        delimiter=',',
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        doublequote=True,
        escapechar=None,  # Not needed with doublequote and QUOTE_MINIMAL
        skipinitialspace=True,
        strict=True,
    )

    return next(rdr)


def load_dict_str_str(raw: str) -> Dict[str, str]:
    """
    Returns a mapping from string to string

    Configuring this in the environment means using logfmt
    """
    return _logfmt.parse_line(raw)


def load_binary_file_from_path(raw: str) -> bytes:
    try:
        with open(raw, 'rb') as fil:
            return fil.read()
    except FileNotFoundError:
        raise ValueError(f'File not found: {raw}')
    except IsADirectoryError:
        raise ValueError(f'Unexpected directory: {raw}')
    except PermissionError:
        raise ValueError(f'No permissions to read: {raw}')


def load_ascii_file_from_path(raw: str) -> str:
    bts = load_binary_file_from_path(raw)

    try:
        return bts.decode('ASCII')
    except ValueError:
        raise ValueError(f'Could not decode as ASCII: {raw}')


def load_utf8_file_from_path(raw: str) -> str:
    bts = load_binary_file_from_path(raw)

    try:
        return bts.decode('UTF-8')
    except ValueError:
        raise ValueError(f'Could not decode as UTF-8: {raw}')


def load_pem_file_from_path(
    raw: str,
    min_data_count: int = 0,
    max_data_count: Optional[int] = None,
) -> List[str]:
    """
    Loads a file with PEM encoded data

    See https://www.rfc-editor.org/rfc/rfc4880

    Note that this function returns a list of strings, as
    a file may have more than one PEM encoded data in it.
    """
    txt = load_ascii_file_from_path(raw)

    result: List[str] = []

    data: List[str] = []
    for line in txt.splitlines():
        if data:
            data.append(line)

            if line.startswith('-----END ') and line.endswith('-----'):
                # Parsers MAY disregard the label
                result.append('\n'.join(data) + '\n')
                data = []
        else:
            if line.startswith('-----BEGIN ') and line.endswith('-----'):
                data.append(line)

    if not result:
        raise ValueError(f'No valid PEM encoded data found: {raw}')

    if min_data_count == 0 and max_data_count is None:
        return result

    if max_data_count is None:
        msg = f'Expected at least {min_data_count} PEM encoded data: {raw}'
    else:
        msg = (
            f'Expected between {min_data_count} and {max_data_count}'
            f' PEM encoded data: {raw}'
        )

    if len(result) < min_data_count:
        raise ValueError(msg)

    if max_data_count is not None and max_data_count < len(result):
        raise ValueError(msg)

    return result


def load_pem_data_from_path(raw: str) -> str:
    """
    Short-hand function for when your PEM file only has one data
    """
    return load_pem_file_from_path(raw, min_data_count=1, max_data_count=1)[0]
