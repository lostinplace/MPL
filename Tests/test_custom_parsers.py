from parsita import Success, lit, Failure, opt

from Parser.CustomParsers import excluding, at_least, check, best
from Parser.expression_parser import ExpressionParsers


def test_single_parse():
    expression = "alfred - (bruce & jack)"
    result = ExpressionParsers.expression.parse(expression)
    assert isinstance(result, Success)


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
    tmp = check("ok") & "ok ready to go"
    result = tmp.parse("ok ready to go")
    assert result == Success(['ok', "ok ready to go"])


def test_best_alternative_parser():
    non_greedy = (lit("ok") & opt("+")) | (lit("ok") & opt("-"))
    tmp_greedy = best(non_greedy)

    result_1 = non_greedy.parse("ok-")
    assert isinstance(result_1, Failure)
    result_2 = tmp_greedy.parse("ok-")
    assert result_2 == Success(['ok', ['-']])