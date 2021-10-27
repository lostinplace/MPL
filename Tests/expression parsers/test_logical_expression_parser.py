import unittest

from Parser.ExpressionParsers.logical_expression_parser import LogicalOperation, LogicalExpression, \
    LogicalExpressionParsers
from Parser.ExpressionParsers.state_expression_parser import StateExpressionParsers, StateOperation, StateExpression
from Parser.Tokenizers.operator_tokenizers import StateOperator, LogicalOperator
from Parser.Tokenizers.simple_value_tokenizer import NumberToken
from Tests import collect_parsing_expectations, qle, qdae


class LogicalExpresssionTests(unittest.TestCase):

    def test_logical_expression_parsers(self):
        self.maxDiff = None
        expectations = {
            "A == 1": LogicalExpression([
                LogicalOperation(
                    qle('A'),
                    LogicalOperator('==')
                ),
                LogicalOperation(
                    qdae(1),
                    None
                ),
            ])
        }

        results = collect_parsing_expectations(expectations, LogicalExpressionParsers.expression)
        for result in results:
            result = result.as_strings()

            self.assertEquals(result.actual, result.expected)
