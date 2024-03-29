from typing import Dict

# Taken from https://github.com/jkakar/logfmt-python
# and then https://github.com/wlonk/logfmt-python
# But they don't provide the parser anymore
# See https://lucumr.pocoo.org/2024/3/26/rust-cdo/
# I made it signficantly more strict, since configuration
# is not a place for skipping over bad input

GARBAGE = 0
KEY = 1
EQUAL = 2
IVALUE = 3
QVALUE = 4


def parse_line(line: str) -> Dict[str, str]:
    output: Dict[str, str] = {}
    key: str = ''
    value: str = ''
    escaped = False
    state: int = GARBAGE

    for i, c in enumerate(line):
        i += 1

        if state == GARBAGE:
            if '0' <= c <= '9' or 'A' <= c <= 'Z' or 'a' <= c <= 'z':
                key = c
                state = KEY
                continue

            if ' ' == c:
                continue

            raise ValueError(f'Unexpected {c} at {i}')

        if state == KEY:
            if '0' <= c <= '9' or 'A' <= c <= 'Z' or 'a' <= c <= 'z':
                key += c
                continue

            if c == "=":
                state = EQUAL
                continue

            raise ValueError(f'Unexpected {c} at {i}')

        if state == EQUAL:
            if c == '"':
                value = ''
                escaped = False
                state = QVALUE
                continue

            if c > " ":
                value = c
                state = IVALUE
                continue

            raise ValueError(f'Unexpected {c} at {i}')

        if state == IVALUE:
            if c == ' ':
                output[key] = value
                state = GARBAGE
                continue

            if c > " ":
                value += c
                continue

            raise ValueError(f'Unexpected {c} at {i}')

        if state == QVALUE:
            if c == "\\":
                if escaped:
                    escaped = False
                    value += c
                else:
                    escaped = True
                continue

            if c == '"':
                if escaped:
                    escaped = False
                    value += c
                else:
                    output[key] = value
                    state = GARBAGE
                continue

            # Within a quoted value, any character goes
            value += c
            continue

    if state == KEY:
        raise ValueError(f'Missing value for {key}')

    if state == EQUAL:
        output[key] = ''

    if state == IVALUE:
        output[key] = value

    if state == QVALUE:
        raise ValueError(f'Missing end quote for {key}')

    return output
