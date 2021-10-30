from typing import Dict, Any

from parsita import Success, lit, Failure, opt, Parser, TextParsers
from parsita.state import Input, Output

from lib.CustomParsers import excluding, at_least, check, best, track, repwksep, debug, ParseResult


def test_exclude_parser():
    tmp_parser = excluding(lit('->')) & '->'
    result = tmp_parser.parse("example ->")
    assert result == Success(['example ', '->'])
    result_2 = tmp_parser.parse("-> dsf")
    assert isinstance(result_2, Failure)


def test_at_least_parser():
    pattern = '+-'
    tmp_parser = at_least(3, pattern)
    for i in range(10):
        test = pattern * i
        result = tmp_parser.parse(test)
        if(i<3):
            assert isinstance(result, Failure)
        else:
            expected = [pattern for _ in range(i)]
            assert result == Success(expected)


def test_check_parser():
    tmp: Parser[Input, Output] = check("ok") & "ok ready to go"
    result = tmp.parse("ok ready to go")
    assert result == Success(['ok', "ok ready to go"])


def test_best_alternative_parser():
    non_greedy = (lit("ok") & opt("+")) | (lit("ok") & opt("-"))
    tmp_greedy = best(non_greedy)

    result_1 = non_greedy.parse("ok-")
    assert isinstance(result_1, Failure)
    result_2 = tmp_greedy.parse("ok-")
    assert result_2 == Success(['ok', ['-']])


def test_track_parser():
    parser = lit('12345') >> track(lit('678') << '90') << '12345'

    value = '123456789012345'

    result = parser.parse(value)

    assert result == Success(
        ParseResult(value='678', start=5, ParserName=None)
    )


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


def test_repwksep_parser():
    test_parser:Parser[Input, Input] = repwksep(lit('ok') | 'not ok', lit(',') | '+')

    expectations = {
        'ok,ok,not ok': [('ok', ','), ('ok', ','), 'not ok'],
        'not ok+ok,ok': [('not ok', '+'), ('ok', ','), 'ok'],
        'not ok+ok,': Failure,
    }

    assert_parsing_expectations(expectations, test_parser)

blah = 'testing'


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
    assert blah == 'testing'

