from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression, AssignmentExpressionParsers
from Parser.Tokenizers.operator_tokenizers import AssignmentOperator

from Tests import qdae, qle, collect_parsing_expectations


def test_assignment_expression_parsers():
    expectations = {
        "a = 1": AssignmentExpression(
            qle('a'),
            qdae(1),
            AssignmentOperator('=')
        ),
        'a:TEST += 12 + 1': AssignmentExpression(
            qle('a:TEST'),
            qdae((12, '+'), 1),
            AssignmentOperator('+=')
        ),
        "help:Me /= 1+(2-3)*4": AssignmentExpression(
            qle('help:Me'),
            qdae((1, '+'), (qdae((2, '-'), 3), '*'), 4),
            AssignmentOperator('/=')
        ),
    }

    results = collect_parsing_expectations(expectations, AssignmentExpressionParsers.expression)
    for actual, expected, input in results:
        assert actual == expected

