from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression, AssignmentExpressionParsers
from Parser.Tokenizers.operator_tokenizers import AssignmentOperator

from Tests import qdae, qre, collect_parsing_expectations


def test_assignment_expression_parsers():
    expectations = {
        "help:Me /= 1+(2-3)*4": AssignmentExpression(
            qre('help:Me'),
            qdae((1, '+'), (qdae((2, '-'), 3), '*'), 4),
            AssignmentOperator('/=')
        ),
        "a = 1": AssignmentExpression(
            qre('a'),
            qdae(1),
            AssignmentOperator('=')
        ),
        'a:TEST += 12 + 1': AssignmentExpression(
            qre('a:TEST'),
            qdae((12, '+'), 1),
            AssignmentOperator('+=')
        ),
    }

    results = collect_parsing_expectations(expectations, AssignmentExpressionParsers.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected

