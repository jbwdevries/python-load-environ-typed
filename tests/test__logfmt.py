import unittest
import load_environ_typed._logfmt as sut


class TestParseLine(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual({}, sut.parse_line(''))

    def test_one(self) -> None:
        self.assertEqual({'a': ''}, sut.parse_line('a='))
        self.assertEqual({'a': '1'}, sut.parse_line('a=1'))
        self.assertEqual({'a': 'b'}, sut.parse_line('a=b'))
        self.assertEqual({'a': 'b'}, sut.parse_line('a=b '))

        self.assertEqual({'foo': ''}, sut.parse_line('foo='))
        self.assertEqual({'foo': '1234'}, sut.parse_line('foo=1234'))
        self.assertEqual({'foo': 'bar'}, sut.parse_line('foo=bar'))

        self.assertEqual({'foo': ''}, sut.parse_line('foo=""'))
        self.assertEqual({'foo': '1234'}, sut.parse_line('foo="1234"'))
        self.assertEqual({'foo': 'bar'}, sut.parse_line('foo="bar"'))

        self.assertEqual(
            {'foo': 'bar \\ boza'},
            sut.parse_line('foo="bar \\\\ boza"'),
        )
        self.assertEqual(
            {'foo': 'bar " boza'},
            sut.parse_line('foo="bar \\" boza"'),
        )

    def test_multiple(self) -> None:
        self.assertEqual(
            {
                'a': '1',
                'msg': 'Hello, world!',
                'quoted': 'And I said, "That\'s what he said!"',
            },
            sut.parse_line(
                'a=1'
                ' msg="Hello, world!"'
                ' quoted="And I said, \\"That\'s what he said!\\""',
            )
        )

    def test_errors(self) -> None:
        with self.assertRaisesRegex(ValueError, 'Unexpected @ at 1'):
            sut.parse_line('@')

        with self.assertRaisesRegex(ValueError, 'Unexpected @ at 5'):
            sut.parse_line('a=1 @')

        with self.assertRaisesRegex(ValueError, 'Unexpected @ at 2'):
            sut.parse_line('a@')

        with self.assertRaisesRegex(ValueError, 'Unexpected @ at 6'):
            sut.parse_line('a=1 b@')

        with self.assertRaisesRegex(ValueError, 'Unexpected \t at 3'):
            sut.parse_line('a=\t')

        with self.assertRaisesRegex(ValueError, 'Unexpected \t at 7'):
            sut.parse_line('a=1 b=\t')

        with self.assertRaisesRegex(ValueError, 'Unexpected \t at 4'):
            sut.parse_line('a=1\t')

        with self.assertRaisesRegex(ValueError, 'Unexpected \t at 8'):
            sut.parse_line('a=1 b=1\t')

        with self.assertRaisesRegex(ValueError, 'Missing value for a'):
            sut.parse_line('a')

        with self.assertRaisesRegex(ValueError, 'Missing value for b'):
            sut.parse_line('a=1 b')

        with self.assertRaisesRegex(ValueError, 'Missing end quote for b'):
            sut.parse_line('a=1 b="123')
