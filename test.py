from typing import NamedTuple

import unittest
from dataclasses import dataclass
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
    NT_PROP: int = 4


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
    DC_PROP: int = 4


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
            'No value in environ for required property DB_NAME '
            'of type builtins.str',
            str(cm.exception))

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
        self.assertEqual(environ.NT_PROP, 4)

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
        self.assertEqual(environ.DC_PROP, 4)


"""
Running the tests as main
"""


if __name__ == '__main__':
    unittest.main()
