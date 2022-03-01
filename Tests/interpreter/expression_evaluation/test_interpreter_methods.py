from Tests import quick_parse
from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.interpreter.expression_evaluation.interpreters import create_expression_interpreter


def test_get_references_from_assignment():
    expectations = {
        'a=b+1': {Ref('a'), Ref('b')},
        'c += delta & echo + 5 - <sierra>': {Ref('delta'), Ref('echo'), Ref('sierra'), Ref('c')},
        'source thing += testing a complex string ^ <complex trigger>': {
            Ref('testing a complex string'),
            Ref('complex trigger'),
            Ref('source thing')
        },
        'd = `test`': {Ref('d')},
    }

    for expr_input, expected in expectations.items():
        expression = quick_parse(AssignmentExpression, expr_input)
        interpreter = create_expression_interpreter(expression)
        result = interpreter.references
        assert result == expected


def test_get_references_from_query():
    expectations = {
        'a&b': {Ref('a'), Ref('b')},
        'a&b|c': {Ref('a'), Ref('b'), Ref('c')},
        '<trigger thing>&<other thing> | simple + 5': {Ref('trigger thing'), Ref('other thing'), Ref('simple')},
    }

    for expr_input, expected in expectations.items():
        expression = quick_parse(QueryExpression, expr_input)
        interpreter = create_expression_interpreter(expression)
        result = interpreter.references
        assert result == expected


def test_get_references_from_scenario():
    expectations = {
        '%{a}': {Ref('a')},
        '%{a & b}': {Ref('a'), Ref('b')},
        '%{a & b | c}': {Ref('a'), Ref('b'), Ref('c')},
        '%{<trigger thing> & <other thing> | simple + 5}': {Ref('trigger thing'), Ref('other thing'), Ref('simple')},
    }

    for expr_input, expected in expectations.items():
        expression = quick_parse(ScenarioExpression, expr_input)
        interpreter = create_expression_interpreter(expression)
        result = interpreter.references
        assert result == expected


def test_get_references_from_target():
    expectations = {
        'a': {Ref('a')},
        'a & b': {Ref('a'), Ref('b')},
        'a & b | c': {Ref('a'), Ref('b'), Ref('c')},
        '<trigger thing> & <other thing> | simple + 5': {Ref('trigger thing'), Ref('other thing'), Ref('simple')},
    }

    for expr_input, expected in expectations.items():
        expression = quick_parse(QueryExpression, expr_input)
        interpreter = create_expression_interpreter(expression, True)
        result = interpreter.references
        assert result == expected
