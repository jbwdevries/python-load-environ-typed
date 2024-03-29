from typing import List, NamedTuple, Optional

import datetime
import sys
import unittest
from dataclasses import dataclass, FrozenInstanceError
from functools import partial
from pathlib import Path

import load_environ_typed as sut
from load_environ_typed import loaders as sut_loaders

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
Tests for the extra loaders
"""


class TestExtraLoaders(unittest.TestCase):
    def test_load_bool_or_int(self) -> None:
        assert 0 == sut_loaders.load_bool_or_int('0')
        assert -124 == sut_loaders.load_bool_or_int('-124')
        assert True is sut_loaders.load_bool_or_int('true')
        assert False is sut_loaders.load_bool_or_int('FalSE')

        with self.assertRaises(ValueError):
            sut_loaders.load_bool_or_int('hello')

    def test_load_bool_or_str(self) -> None:
        assert '' == sut_loaders.load_bool_or_str('')
        assert '?' == sut_loaders.load_bool_or_str('?')
        assert 'hello' == sut_loaders.load_bool_or_str('hello')
        assert True is sut_loaders.load_bool_or_str('true')
        assert False is sut_loaders.load_bool_or_str('FalSE')

    def test_load_bool_or_path(self) -> None:
        assert Path('') == sut_loaders.load_bool_or_path('')
        assert Path('?') == sut_loaders.load_bool_or_path('?')
        assert Path('hello') == sut_loaders.load_bool_or_path('hello')
        assert True is sut_loaders.load_bool_or_path('true')
        assert False is sut_loaders.load_bool_or_path('FalSE')

    def test_load_list_int(self) -> None:
        assert [] == sut_loaders.load_list_int('')
        assert [1] == sut_loaders.load_list_int('1')
        assert [1] == sut_loaders.load_list_int('  1   ')
        assert [1, 2] == sut_loaders.load_list_int('1,2')
        assert [1, 2] == sut_loaders.load_list_int('1, 2')
        assert [-100, 0, 100] == sut_loaders.load_list_int('-100,0,100')

        with self.assertRaises(ValueError):
            sut_loaders.load_list_int('1,2,a')

    def test_load_list_str(self) -> None:
        assert [] == sut_loaders.load_list_str('')
        assert ['1'] == sut_loaders.load_list_str('1')
        assert ['1'] == sut_loaders.load_list_str('    1')
        assert ['1', '2'] == sut_loaders.load_list_str('1,2')
        assert ['1', '2'] == sut_loaders.load_list_str('1, 2')
        assert ['-100', '0', '100'] == sut_loaders.load_list_str('-100,0,100')
        assert ['1', '2', 'a'] == sut_loaders.load_list_str('1,2,a')
        assert ['1', '2', 'a'] == sut_loaders.load_list_str('1,"2",a')
        assert ['1', ' 2 ', 'a'] == sut_loaders.load_list_str('1," 2 ",a')

        assert ['1', '2,a'] == sut_loaders.load_list_str('1,"2,a"')

    def test_load_binary_file_from_path_not_found(self) -> None:
        @dataclass
        class EnvironFile:
            prop: bytes

        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(
                EnvironFile,
                environ={
                    'PROP': './file-not-found.404',
                },
                loaders={
                    'prop': sut_loaders.load_binary_file_from_path,
                },
            )

        self.assertIn(
            'ValueError for field PROP of type builtins.bytes: '
            'File not found: ./file-not-found.404',
            str(cm.exception))

    def test_load_binary_file_from_path_directory(self) -> None:
        @dataclass
        class EnvironFile:
            prop: bytes

        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(
                EnvironFile,
                environ={
                    'PROP': './load_environ_typed',
                },
                loaders={
                    'prop': sut_loaders.load_binary_file_from_path,
                },
            )

        self.assertIn(
            'ValueError for field PROP of type builtins.bytes: '
            'Unexpected directory: ./load_environ_typed',
            str(cm.exception))

    def test_load_binary_file_from_path_ok(self) -> None:
        @dataclass
        class EnvironFile:
            prop: bytes

        environ = sut.load(
            EnvironFile,
            environ={
                'PROP': './LICENSE.txt',
            },
            loaders={
                'prop': sut_loaders.load_binary_file_from_path,
            },
        )

        assert b'WITHOUT WARRANTY' in environ.prop

    def test_load_ascii_from_path_invalid_encoding(self) -> None:
        @dataclass
        class EnvironFile:
            prop: str

        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(
                EnvironFile,
                environ={
                    'PROP': './tests/utf8.txt',
                },
                loaders={
                    'prop': sut_loaders.load_ascii_file_from_path,
                },
            )

        self.assertIn(
            'ValueError for field PROP of type builtins.str: '
            'Could not decode as ASCII: ./tests/utf8.txt',
            str(cm.exception))

    def test_load_ascii_file_from_path_ok(self) -> None:
        @dataclass
        class EnvironFile:
            prop: str

        environ = sut.load(
            EnvironFile,
            environ={
                'PROP': './LICENSE.txt',
            },
            loaders={
                'prop': sut_loaders.load_ascii_file_from_path,
            },
        )

        assert 'WITHOUT WARRANTY' in environ.prop

    def test_load_utf8_from_path_invalid_encoding(self) -> None:
        @dataclass
        class EnvironFile:
            prop: str

        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(
                EnvironFile,
                environ={
                    'PROP': './tests/numbers.bin',
                },
                loaders={
                    'prop': sut_loaders.load_utf8_file_from_path,
                },
            )

        self.assertIn(
            'ValueError for field PROP of type builtins.str: '
            'Could not decode as UTF-8: ./tests/numbers.bin',
            str(cm.exception))

    def test_load_utf8_file_from_path_ok(self) -> None:
        @dataclass
        class EnvironFile:
            prop: str

        environ = sut.load(
            EnvironFile,
            environ={
                'PROP': './tests/utf8.txt',
            },
            loaders={
                'prop': sut_loaders.load_utf8_file_from_path,
            },
        )

        assert '\u864e' in environ.prop

    def test_load_pem_from_path_no_data(self) -> None:
        @dataclass
        class EnvironFile:
            prop: List[str]

        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(
                EnvironFile,
                environ={
                    'PROP': './LICENSE.txt',
                },
                loaders={
                    'prop': sut_loaders.load_pem_file_from_path,
                },
            )

        self.assertIn(
            'ValueError for field PROP of type typing.List[str]: '
            'No valid PEM encoded data found: ./LICENSE.txt',
            str(cm.exception))

    def test_load_pem_from_path_too_little_data(self) -> None:
        @dataclass
        class EnvironFile:
            prop: List[str]

        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(
                EnvironFile,
                environ={
                    'PROP': './tests/pem2.txt',
                },
                loaders={
                    'prop': partial(sut_loaders.load_pem_file_from_path,
                                    min_data_count=3),
                },
            )

        self.assertIn(
            'ValueError for field PROP of type typing.List[str]: '
            'Expected at least 3 PEM encoded data: ./tests/pem2.txt',
            str(cm.exception))

    def test_load_pem_from_path_too_much_data(self) -> None:
        @dataclass
        class EnvironFile:
            prop: List[str]

        with self.assertRaises(sut.LoadEnvironmentException) as cm:
            sut.load(
                EnvironFile,
                environ={
                    'PROP': './tests/pem2.txt',
                },
                loaders={
                    'prop': partial(sut_loaders.load_pem_file_from_path,
                                    max_data_count=1),
                },
            )

        self.assertIn(
            'ValueError for field PROP of type typing.List[str]: '
            'Expected between 0 and 1 PEM encoded data: ./tests/pem2.txt',
            str(cm.exception))

    def test_load_pem_file_from_path_ok(self) -> None:
        @dataclass
        class EnvironFile:
            prop: List[str]

        environ = sut.load(
            EnvironFile,
            environ={
                'PROP': './tests/pem2.txt',
            },
            loaders={
                'prop': sut_loaders.load_pem_file_from_path,
            },
        )

        assert 2 == len(environ.prop)
        assert 'dlHJS\n7cI7' in environ.prop[0]
        assert 'EFjAU\nBggr' in environ.prop[1]

        assert environ.prop[0].startswith('-----BEGIN CERTIFICATE-----\n')
        assert environ.prop[0].endswith('\n-----END CERTIFICATE-----\n')
        assert environ.prop[1].startswith('-----BEGIN CERTIFICATE-----\n')
        assert environ.prop[1].endswith('\n-----END CERTIFICATE-----\n')

    def test_load_pem_data_from_path_ok(self) -> None:
        @dataclass
        class EnvironFile:
            prop: List[str]

        environ = sut.load(
            EnvironFile,
            environ={
                'PROP': './tests/pem1.txt',
            },
            loaders={
                'prop': sut_loaders.load_pem_data_from_path,
            },
        )

        assert 'dlHJS\n7cI7' in environ.prop


"""
Running the tests as main
"""


if __name__ == '__main__':
    unittest.main()
