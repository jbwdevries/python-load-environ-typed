import unittest
from pathlib import Path

import load_environ_typed.loaders as sut


class TestLoaders(unittest.TestCase):
    def test_load_bool_or_int(self) -> None:
        self.assertEqual(0, sut.load_bool_or_int('0'))
        self.assertEqual(-124, sut.load_bool_or_int('-124'))
        self.assertIs(True, sut.load_bool_or_int('true'))
        self.assertIs(False, sut.load_bool_or_int('FalSE'))

        with self.assertRaises(ValueError):
            sut.load_bool_or_int('hello')

    def test_load_bool_or_str(self) -> None:
        self.assertEqual('', sut.load_bool_or_str(''))
        self.assertEqual('?', sut.load_bool_or_str('?'))
        self.assertEqual('hello', sut.load_bool_or_str('hello'))
        self.assertIs(True, sut.load_bool_or_str('true'))
        self.assertIs(False, sut.load_bool_or_str('FalSE'))

    def test_load_bool_or_path(self) -> None:
        self.assertEqual(Path(''), sut.load_bool_or_path(''))
        self.assertEqual(Path('?'), sut.load_bool_or_path('?'))
        self.assertEqual(Path('hello'), sut.load_bool_or_path('hello'))
        self.assertIs(True, sut.load_bool_or_path('true'))
        self.assertIs(False, sut.load_bool_or_path('FalSE'))

    def test_load_list_int(self) -> None:
        self.assertEqual([], sut.load_list_int(''))
        self.assertEqual([1], sut.load_list_int('1'))
        self.assertEqual([1], sut.load_list_int('  1   '))
        self.assertEqual([1, 2], sut.load_list_int('1,2'))
        self.assertEqual([1, 2], sut.load_list_int('1, 2'))
        self.assertEqual([-100, 0, 100], sut.load_list_int('-100,0,100'))

        with self.assertRaises(ValueError):
            sut.load_list_int('1,2,a')

    def test_load_list_str(self) -> None:
        self.assertEqual([], sut.load_list_str(''))
        self.assertEqual(['1'], sut.load_list_str('1'))
        self.assertEqual(['1'], sut.load_list_str('    1'))
        self.assertEqual(['1', '2'], sut.load_list_str('1,2'))
        self.assertEqual(['1', '2'], sut.load_list_str('1, 2'))
        self.assertEqual(['-100', '0', '100'], sut.load_list_str('-100,0,100'))
        self.assertEqual(['1', '2', 'a'], sut.load_list_str('1,2,a'))
        self.assertEqual(['1', '2', 'a'], sut.load_list_str('1,"2",a'))
        self.assertEqual(['1', ' 2 ', 'a'], sut.load_list_str('1," 2 ",a'))
        self.assertEqual(['1', '2,a'], sut.load_list_str('1,"2,a"'))

    def test_load_dict_str_str(self) -> None:
        self.assertEqual({}, sut.load_dict_str_str(''))
        self.assertEqual({'a': '1'}, sut.load_dict_str_str('a=1'))
        self.assertEqual(
            {'a': '1', 'b': '9'},
            sut.load_dict_str_str('a=1  b=9'),
        )

    def test_load_binary_file_from_path_not_found(self) -> None:
        with self.assertRaises(ValueError) as cm:
            sut.load_binary_file_from_path('./file-not-found.404')

        self.assertEqual(
            'File not found: ./file-not-found.404',
            str(cm.exception))

    def test_load_binary_file_from_path_directory(self) -> None:
        with self.assertRaises(ValueError) as cm:
            sut.load_binary_file_from_path('./load_environ_typed')

        self.assertIn(
            'Unexpected directory: ./load_environ_typed',
            str(cm.exception))

    def test_load_binary_file_from_path_ok(self) -> None:
        self.assertIn(
            b'WITHOUT WARRANTY',
            sut.load_binary_file_from_path('./LICENSE.txt')
        )

    def test_load_ascii_from_path_invalid_encoding(self) -> None:
        with self.assertRaises(ValueError) as cm:
            sut.load_ascii_file_from_path('./tests/utf8.txt')

        self.assertIn(
            'Could not decode as ASCII: ./tests/utf8.txt',
            str(cm.exception))

    def test_load_ascii_file_from_path_ok(self) -> None:
        self.assertIn(
            'WITHOUT WARRANTY',
            sut.load_ascii_file_from_path('./LICENSE.txt'),
        )

    def test_load_utf8_from_path_invalid_encoding(self) -> None:
        with self.assertRaises(ValueError) as cm:
            sut.load_utf8_file_from_path('./tests/numbers.bin')

        self.assertIn(
            'Could not decode as UTF-8: ./tests/numbers.bin',
            str(cm.exception))

    def test_load_utf8_file_from_path_ok(self) -> None:
        self.assertIn(
            '\u864e',
            sut.load_utf8_file_from_path('./tests/utf8.txt'),
        )

    def test_load_pem_from_path_no_data(self) -> None:
        with self.assertRaises(ValueError) as cm:
            sut.load_pem_file_from_path('./LICENSE.txt')

        self.assertIn(
            'No valid PEM encoded data found: ./LICENSE.txt',
            str(cm.exception))

    def test_load_pem_from_path_too_little_data(self) -> None:
        with self.assertRaises(ValueError) as cm:
            sut.load_pem_file_from_path('./tests/pem2.txt', min_data_count=3)

        self.assertIn(
            'Expected at least 3 PEM encoded data: ./tests/pem2.txt',
            str(cm.exception))

    def test_load_pem_from_path_too_much_data(self) -> None:
        with self.assertRaises(ValueError) as cm:
            sut.load_pem_file_from_path('./tests/pem2.txt', max_data_count=1)

        self.assertIn(
            'Expected between 0 and 1 PEM encoded data: ./tests/pem2.txt',
            str(cm.exception))

    def test_load_pem_file_from_path_ok(self) -> None:
        data_list = sut.load_pem_file_from_path('./tests/pem2.txt')

        self.assertEqual(2, len(data_list))
        self.assertIn('dlHJS\n7cI7', data_list[0])
        self.assertIn('EFjAU\nBggr', data_list[1])

        self.assertTrue(
            data_list[0].startswith('-----BEGIN CERTIFICATE-----\n')
        )
        self.assertTrue(
            data_list[0].endswith('\n-----END CERTIFICATE-----\n')
        )
        self.assertTrue(
            data_list[1].startswith('-----BEGIN CERTIFICATE-----\n')
        )
        self.assertTrue(
            data_list[1].endswith('\n-----END CERTIFICATE-----\n')
        )

    def test_load_pem_data_from_path_ok(self) -> None:
        assert 'dlHJS\n7cI7' in sut.load_pem_data_from_path('./tests/pem1.txt')
