import unittest

from Parser.ExpressionParsers.logical_expression_parser import LogicalOperation, LogicalExpression, \
    LogicalExpressionParsers
from Parser.ExpressionParsers.state_expression_parser import StateExpressionParsers, StateOperation, StateExpression
from Parser.Tokenizers.operator_tokenizers import StateOperator, LogicalOperator
from Parser.Tokenizers.simple_value_tokenizer import NumberToken
from Tests import collect_parsing_expectations, qle, qdae


class LogicalExpresssionTests(unittest.TestCase):
    def test_logical_expression_parsers(self):
        # TODO:  need more tests
        self.maxDiff = None
        expectations = {
            "a && (brett + 7 != 4) || d": LogicalExpression([
                LogicalOperation(
                    qle('a'),
                    LogicalOperator('&&')
                ),
                LogicalOperation(
                    LogicalExpression([
                        LogicalOperation(
                            qdae(
                                (qle('brett', 6), '+'),
                                7
                            ),
                            LogicalOperator('!=')
                        ),
                        LogicalOperation(
                            qdae(4), None
                        ),

                    ]),
                    LogicalOperator('||')
                ),
                LogicalOperation(
                    qle('d', 25),
                    None
                ),
            ]),
            "A == 1": LogicalExpression([
                LogicalOperation(
                    qle('A'),
                    LogicalOperator('==')
                ),
                LogicalOperation(
                    qdae(1),
                    None
                ),
            ]),
            "A && B != C || D": LogicalExpression([
                LogicalOperation(
                    qle('A'),
                    LogicalOperator('&&')
                ),
                LogicalOperation(
                    qle('B', 5),
                    LogicalOperator('!=')
                ),
                LogicalOperation(
                    qle('C', 10),
                    LogicalOperator('||')
                ),
                LogicalOperation(
                    qle('D', 15),
                    None
                ),
            ]),
        }

        results = collect_parsing_expectations(expectations, LogicalExpressionParsers.expression)
        for result in results:
            result = result.as_strings()

            self.assertEquals(result.actual, result.expected)
