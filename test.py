from typing import NamedTuple, Optional

import datetime
import sys
import unittest
from dataclasses import dataclass, FrozenInstanceError
from pathlib import Path

import load_environ_typed as sut

"""
Example for what you'd do when you need to use a loader for a type

Assuming you don't have the ability to add static methods to the class
"""


class PasswordFromFile:
    def __init__(self, path: Path, encoding: str) -> None:
        self.path = path
        with open(path, 'r', encoding=encoding) as fil:
            self.secret = fil.read()


def password_loader(raw_path: str) -> PasswordFromFile:
    return PasswordFromFile(Path(raw_path), 'utf-8')


"""
Second for what you'd do when you need to use a loader for a type

This time, when you do want to have a static method on the class
"""


class SecretFromFile:
    def __init__(self, path: Path, encoding: str) -> None:
        self.path = path
        with open(path, 'r', encoding=encoding) as fil:
            self.secret = fil.read()

    @staticmethod
    def load_environ_typed(env: str) -> 'SecretFromFile':
        return SecretFromFile(Path(env), 'utf-8')


"""
Example environment using a NamedTuple
"""


class EnvironNt(NamedTuple):
    DB_NAME: str
    DB_PORT: int
    DB_PASSWORD: PasswordFromFile
    DB_USE_TRANSACTIONS: bool
    DB_CA_FILE: Path
    MQTT_PASSWORD: SecretFromFile
    AAA_SORT_TEST: str
    NT_FIELD: int = 4


"""
Example environment using a dataclass
"""


@dataclass
class EnvironDc:
    DB_NAME: str
    DB_PORT: int
    DB_PASSWORD: PasswordFromFile
    DB_USE_TRANSACTIONS: bool
    DB_CA_FILE: Path
    MQTT_PASSWORD: SecretFromFile
    AAA_SORT_TEST: str
    DC_FIELD: int = 4


"""
The acual test cases, from low level to high level
"""


class TestLoad(unittest.TestCase):
    def test_must_be_named_tupled_or_dataclass(self) -> None:
        with self.assertRaises(RuntimeError):
            sut.load(PasswordFromFile)

    def test_error_missing_value(self) -> None:
        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(
                EnvironNt,
                environ={},
                defaults={},
            )

        self.assertIn(
            'No value in environ for required field DB_NAME '
            'of type builtins.str',
            str(cm.exception))

    def test_field_name_cleanup(self) -> None:
        @dataclass
        class EnvironType:
            var: bool

        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(EnvironType, environ={})

        self.assertIn(
            'No value in environ for required field VAR '
            'of type builtins.bool',
            str(cm.exception))

        environ = sut.load(EnvironType, environ={'VAR': 'true'})
        self.assertEqual(environ.var, True)

        environ = sut.load(EnvironType, environ={}, defaults={'VAR': 'true'})
        self.assertEqual(environ.var, True)

        environ = sut.load(EnvironType, environ={'RAV': 'true'},
                           field_name_to_var_name=lambda x: x[::-1].upper())
        self.assertEqual(environ.var, True)

    def test_type_bool(self) -> None:
        @dataclass
        class EnvironType:
            VAR: bool

        test_valid_list = [
            ('true', True),
            ('True', True),
            ('tRuE', True),

            ('false', False),
            ('False', False),
            ('fAlSe', False),
        ]

        for (inp, out) in test_valid_list:
            environ = sut.load(EnvironType, environ={'VAR': inp})
            self.assertEqual(environ.VAR, out, f'"{inp}" should be {out}')

        test_invalid_list = [
            '0',
            '1',
            't',
            'f',
        ]

        for inp in test_invalid_list:
            with self.assertRaises(sut.LoadEnvironmentException,
                                   msg=f'"{inp}" should not be valid'):
                sut.load(EnvironType, environ={'VAR': inp})

    def test_type_int(self) -> None:
        @dataclass
        class EnvironType:
            VAR: int

        test_valid_list = [
            ('0', 0),
            ('100', 100),
            ('-100', -100),
        ]

        for (inp, out) in test_valid_list:
            environ = sut.load(EnvironType, environ={'VAR': inp})
            self.assertEqual(environ.VAR, out, f'"{inp}" should be {out}')

        test_invalid_list = [
            '+-123',
            'three fiddy',
            '0.234',
        ]

        for inp in test_invalid_list:
            with self.assertRaises(sut.LoadEnvironmentException,
                                   msg=f'"{inp}" should not be valid'):
                sut.load(EnvironType, environ={'VAR': inp})

    def test_type_str(self) -> None:
        @dataclass
        class EnvironType:
            VAR: str

        test_valid_list = [
            ('0', '0'),
            ('SOMEKEYTHATWORKS', 'SOMEKEYTHATWORKS'),
            ('-100', '-100'),
        ]

        for (inp, out) in test_valid_list:
            environ = sut.load(EnvironType, environ={'VAR': inp})
            self.assertEqual(environ.VAR, out, f'"{inp}" should be {out}')

    def test_type_date(self) -> None:
        @dataclass
        class EnvironType:
            VAR: datetime.date

        test_valid_list = [
            ('2001-01-01', datetime.date(2001, 1, 1), ),
            ('2010-10-10', datetime.date(2010, 10, 10), ),
            ('2100-12-31', datetime.date(2100, 12, 31), ),
        ]

        for (inp, out) in test_valid_list:
            environ = sut.load(EnvironType, environ={'VAR': inp})
            self.assertEqual(environ.VAR, out, f'"{inp}" should be {out}')

        test_invalid_list = [
            '2023',
            'bicycle',
            'true',
        ]

        for inp in test_invalid_list:
            with self.assertRaises(sut.LoadEnvironmentException,
                                   msg=f'"{inp}" should not be valid'):
                sut.load(EnvironType, environ={'VAR': inp})

    def test_type_path(self) -> None:
        @dataclass
        class EnvironType:
            VAR: Path

        test_valid_list = [
            ('/', Path('/'), ),
            ('/etc/passwd', Path('/etc/passwd'), ),
            ('/var/log/nginx', Path('/var/log/nginx'), ),
        ]

        for (inp, out) in test_valid_list:
            environ = sut.load(EnvironType, environ={'VAR': inp})
            self.assertEqual(environ.VAR, out, f'"{inp}" should be {out}')

    def test_type_optional_str(self) -> None:
        @dataclass
        class EnvironType:
            VAR: Optional[str]

        environ = sut.load(EnvironType, environ={})
        self.assertEqual(environ.VAR, None, 'No value given should be None')

        test_valid_list = [
            ('', None, ),
            ('None', None, ),
            ('none', None, ),
            ('nOnE', None, ),
            ('foo', 'foo', ),
            ('baz', 'baz', ),
        ]

        for (inp, out) in test_valid_list:
            environ = sut.load(EnvironType, environ={'VAR': inp})
            self.assertEqual(environ.VAR, out, f'"{inp}" should be {out}')

    def test_type_optional_with_default(self) -> None:
        @dataclass
        class EnvironType:
            VAR: Optional[str] = 'default'

        environ = sut.load(EnvironType, environ={})
        self.assertEqual(environ.VAR, 'default')

        environ = sut.load(EnvironType, environ={'VAR': 'none'})
        self.assertEqual(environ.VAR, None)

    def test_custom_loader_key(self) -> None:
        # Example from README.md

        @dataclass
        class MyEnviron:
            ISO_DATE: datetime.date

        environ = sut.load(MyEnviron, environ={
            'ISO_DATE': '2021-01-01',
        }, loaders={
            'ISO_DATE': datetime.date.fromisoformat,
        })

        self.assertEqual(datetime.date(2021, 1, 1), environ.ISO_DATE)

    def test_custom_loader_type(self) -> None:
        # Example from README.md

        @dataclass
        class MyEnviron:
            ISO_DATE: datetime.date

        environ = sut.load(MyEnviron, environ={
            'ISO_DATE': '2021-01-01',
        }, loaders={
            datetime.date: datetime.date.fromisoformat,
        })

        self.assertEqual(datetime.date(2021, 1, 1), environ.ISO_DATE)

    def test_named_tuple(self) -> None:
        environ = sut.load(
            EnvironNt,
            environ={
                'DB_NAME': 'database',
                'DB_PASSWORD': './password.txt',
                'DB_USE_TRANSACTIONS': 'True',
                'DB_CA_FILE': '/foo/baz/ca.crt',
                'MQTT_PASSWORD': './password.txt',
                'AAA_SORT_TEST': 'zzz',
            },
            defaults={
                'DB_PORT': '3306',
            },
            loaders={
                'DB_PASSWORD': password_loader,
            },
        )

        self.assertEqual(environ.DB_NAME, 'database')
        self.assertEqual(environ.DB_PASSWORD.secret, 'swordfish')
        self.assertEqual(environ.DB_PORT, 3306)
        self.assertEqual(environ.DB_USE_TRANSACTIONS, True)
        self.assertEqual(environ.DB_CA_FILE, Path('/foo/baz/ca.crt'))
        self.assertEqual(environ.AAA_SORT_TEST, 'zzz')
        self.assertEqual(environ.NT_FIELD, 4)

    def test_data_class(self) -> None:
        environ = sut.load(
            EnvironDc,
            environ={
                'DB_NAME': 'database',
                'DB_PASSWORD': './password.txt',
                'DB_USE_TRANSACTIONS': 'True',
                'DB_CA_FILE': '/foo/baz/ca.crt',
                'MQTT_PASSWORD': './password.txt',
                'AAA_SORT_TEST': 'zzz',
            },
            defaults={
                'DB_PORT': '3306',
            },
            loaders={
                'DB_PASSWORD': password_loader,
            },
        )

        self.assertEqual(environ.DB_NAME, 'database')
        self.assertEqual(environ.DB_PASSWORD.secret, 'swordfish')
        self.assertEqual(environ.DB_PORT, 3306)
        self.assertEqual(environ.DB_USE_TRANSACTIONS, True)
        self.assertEqual(environ.DB_CA_FILE, Path('/foo/baz/ca.crt'))
        self.assertEqual(environ.AAA_SORT_TEST, 'zzz')
        self.assertEqual(environ.DC_FIELD, 4)

    def test_frozen(self) -> None:
        @dataclass(frozen=True)
        class FrozenEnviron:
            DB_NAME: str

        environ = sut.load(FrozenEnviron, environ={'DB_NAME': 'database'})

        self.assertEqual(environ.DB_NAME, 'database')

        with self.assertRaises(FrozenInstanceError):
            # mypy already picks this up as an error
            # So we have to ignore it since we want to make sure it works
            environ.DB_NAME = 'tpk'  # type: ignore

    def test_forward_reference_annotation(self) -> None:
        @dataclass
        class FrozenEnviron:
            DB_NAME: 'str'

        environ = sut.load(FrozenEnviron, environ={'DB_NAME': 'database'})

        self.assertEqual(environ.DB_NAME, 'database')

    @unittest.skipIf(sys.version_info < (3, 10), 'Python 3.10+ only')
    def test_pep_604(self) -> None:
        @dataclass
        class FrozenEnviron:
            DB_NAME: 'str | None'

        environ = sut.load(FrozenEnviron, environ={'DB_NAME': 'database'})

        self.assertEqual(environ.DB_NAME, 'database')

    @unittest.skipIf(sys.version_info < (3, 10), 'Python 3.10+ only')
    def test_kw_only(self) -> None:
        @dataclass(kw_only=True)  # type: ignore [call-overload,unused-ignore]
        class FrozenEnviron:
            DB_NAME: str

        environ = sut.load(FrozenEnviron, environ={'DB_NAME': 'database'})

        self.assertEqual(environ.DB_NAME, 'database')


"""
Running the tests as main
"""


if __name__ == '__main__':
    unittest.main()
