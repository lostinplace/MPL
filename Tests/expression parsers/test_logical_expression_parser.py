import unittest

from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, \
    LogicalExpressionParsers, Negation
from Parser.Tokenizers.operator_tokenizers import LogicalOperator
from Tests import collect_parsing_expectations, qre, qdae


def test_logical_expression_parsers():

    expectations = {
        "a && !b": LogicalExpression(
            [
                qre('a'),
                Negation(qre('b'))
            ],
            [LogicalOperator('&&')]
        ),
        "a && !(brett + 7 != 4) || d": LogicalExpression(
            [
                qre('a'),
                Negation(
                    LogicalExpression(
                        [qdae('brett + 7'), qdae('4')],
                        [LogicalOperator("!=")]
                    )
                ),
                qre('d'),
            ],
            [LogicalOperator("&&"), LogicalOperator("||")]
        ),
        "A == 1": LogicalExpression(
            [qre("A"), qdae("1")],
            [LogicalOperator('==')]
        ),
        "A && B != C || D": LogicalExpression(
            [qre("A"), qre("B"), qre("C"), qre("D")],
            [LogicalOperator('&&'), LogicalOperator('!='), LogicalOperator('||')]
        ),
    }

    results = collect_parsing_expectations(expectations, LogicalExpressionParsers.expression)
    for result in results:
        result = result.as_strings()
        assert result.actual == result.expected
