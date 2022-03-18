from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression, AssignmentExpressionParsers
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.Tokenizers.operator_tokenizers import AssignmentOperator
from mpl.Parser.Tokenizers.simple_value_tokenizer import StringToken

from Tests import quick_reference_expression, collect_parsing_expectations, quick_parse


def test_assignment_expression_parsers():
    expectations = {
        'noise = `safe`': AssignmentExpression(
            quick_reference_expression('noise'),
            quick_parse(QueryExpression, '`safe`'),
            AssignmentOperator('=')
        ),
        "help:Me /= 1+(2-3)*4": AssignmentExpression(
            quick_reference_expression('help:Me'),
            quick_parse(QueryExpression, '1+(2-3)*4'),
            AssignmentOperator('/=')
        ),
        "a = 1": AssignmentExpression(
            quick_reference_expression('a'),
            quick_parse(QueryExpression, '1'),
            AssignmentOperator('=')
        ),
        'a:TEST += 12 + 1': AssignmentExpression(
            quick_reference_expression('a:TEST'),
            quick_parse(QueryExpression, '12 + 1'),
            AssignmentOperator('+=')
        ),
    }

    results = collect_parsing_expectations(expectations, AssignmentExpressionParsers.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected

