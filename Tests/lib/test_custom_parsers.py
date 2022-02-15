from typing import Dict, Any

from parsita import Success, lit, Failure, Parser, TextParsers, reg, repsep
from parsita.parsers import RegexParser
from parsita.state import Input, Output

from Tests import collect_parsing_expectations
from mpl.lib.parsers.custom_parsers import excluding, check, debug, back
from mpl.lib.parsers.additive_parsers import track, TrackedValue, TrackingMetadata
from mpl.lib.parsers.repsep2 import repsep2, SeparatedList


def test_exclude_parser():
    tmp_parser = excluding(lit('->')) & '->'
    result = tmp_parser.parse("example ->")
    assert result == Success(['example ', '->'])
    result_2 = tmp_parser.parse("-> dsf")
    assert isinstance(result_2, Failure)


def test_check_parser():
    tmp: Parser[Input, Output] = check("ok") & "ok ready to go"
    result = tmp.parse("ok ready to go")
    assert result == Success(['ok', "ok ready to go"])


def test_track_parser():
    parser = lit('12345') >> track(lit('678') << '90') << '12345'

    value = '123456789012345'

    result = parser.parse(value)

    assert isinstance(result, Success)

    result_value: TrackedValue = result.value

    assert result_value == '678'

    expected_metadata = TrackingMetadata(
        5,
        "'678' << '90'",
        '67890',
        None
    )

    assert result_value.metadata == expected_metadata


def test_track_parser_with_simple_tag():
    integer = reg(r'[-+]?[0-9]+') > int
    parser = 'it is ' >> track(integer, tag='fahrenheit') << ' degrees outside'

    content = 'it is -32 degrees outside'

    result = parser.parse(content)
    assert isinstance(result, Success)
    result_value: TrackedValue = result.value
    assert result_value == -32

    expected_metadata = TrackingMetadata(
        6,
        r"reg(r'[-+]?[0-9]+')",
        '-32',
        'fahrenheit'
    )

    assert result_value.metadata == expected_metadata


def test_track_parser_with_callback_tag():
    parser = lit('this is $') >> track(reg(r'\d+'), lambda _: int(_))

    content = 'this is $150'

    result = parser.parse(content)
    assert isinstance(result, Success)
    result_value: TrackedValue = result.value
    assert result_value == '150'

    expected_metadata = TrackingMetadata(
        9,
        r"reg(r'\d+')",
        '150',
        150
    )

    assert result_value.metadata == expected_metadata


def assert_parsing_expectations(expectations: Dict[str, Any], parser):
    results = []
    for (v, expected_outcome) in expectations.items():
        result = parser.parse(v)

        if expected_outcome is Failure:
            assert type(result) is Failure
            continue
        assert type(result) == Success
        assert result == Success(expected_outcome)
        results.append((v, expected_outcome, result))
    return results


def qsl(values, separators):
    result = SeparatedList(values)
    result.separators = separators
    return result


def test_repsep2_parser_basic():

    test_parser:Parser[Input, Input] = repsep2(lit('ok') | 'not ok', lit(',') | '+')

    expectations = {
        'ok,ok,not ok': qsl(['ok','ok','not ok'], [',',',']),
        'not ok+ok,ok': qsl(['not ok', 'ok', 'ok'], ['+', ',']),
        'not ok+ok,': Failure,
    }

    collect_parsing_expectations(expectations, test_parser)


def test_repsep2_parser_reset():

    content = \
    """
    test1
        test2
            test3
            test4
    test5""".strip('\n')

    expected = (
        ('test1', 4),
        ('test2', 8),
        ('test3', 12),
        ('test4', 12),
        ('test5', 4),
    )

    def processor(result):
        return result, result.metadata.start

    iw = RegexParser(r"[ \t]*", None)
    value = RegexParser(r"test\d", None)
    line = iw >> track(value) > processor

    test_parser = repsep2(line, '\n', reset=True)

    actual = test_parser.parse(content)

    assert actual == Success(expected)


def test_debug_callback():
    result = False

    def debug_cb(parser, reader):
        nonlocal result
        remainder = reader.source[reader.position :]
        result = remainder == "45"
        result &= isinstance(parser.parse(remainder), Failure)
        result &= isinstance(parser.parse("345"), Success)

    class TestParsers(TextParsers):
        a = lit("123")
        b = lit("345")
        c = a & debug(b, callback=debug_cb)

    TestParsers.c.parse("12345")
    assert result
    assert str(TestParsers.c) == "c = a & debug(b)"


def test_lookback():

    expectations = {
        "v/test/bp21": [
            "v",
            "test",
            {'test': 'bp21'},
        ],
        "v/test/bp21/": [
            "v",
            "test",
            {'test': 'bp21'},
            ""
        ],
        "cp//123123": [
            "cp",
            "",
            '123123',
        ],
    }

    identifier = reg('[a-zA-Z0-9]*')
    process_test_id = lambda _: {'test': _}
    test_id = back('test/') >> identifier > process_test_id
    test_parser = repsep(test_id | identifier, '/')

    for result in collect_parsing_expectations(expectations, test_parser):
        assert result.actual == result.expected

