from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression, AssignmentExpressionParsers
from Parser.Tokenizers.operator_tokenizers import AssignmentOperator

from Tests import qdae, qre, collect_parsing_expectations, quick_parse


def test_assignment_expression_parsers():
    expectations = {
        "help:Me /= 1+(2-3)*4": AssignmentExpression(
            qre('help:Me'),
            quick_parse(ArithmeticExpression, '1+(2-3)*4'),
            AssignmentOperator('/=')
        ),
        "a = 1": AssignmentExpression(
            qre('a'),
            quick_parse(ArithmeticExpression, '1'),
            AssignmentOperator('=')
        ),
        'a:TEST += 12 + 1': AssignmentExpression(
            qre('a:TEST'),
            quick_parse(ArithmeticExpression, '12 + 1'),
            AssignmentOperator('+=')
        ),
    }

    results = collect_parsing_expectations(expectations, AssignmentExpressionParsers.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected

