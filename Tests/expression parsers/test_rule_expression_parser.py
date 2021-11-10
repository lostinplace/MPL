from Parser.ExpressionParsers.rule_expression_parser import Rule, RuleExpressionParsers
from Parser.ExpressionParsers.state_expression_parser import StateExpression
from Parser.Tokenizers.operator_tokenizers import MPLOperator

from Tests import qre, collect_parsing_expectations


def test_rule_expression_parsers():
    expectations = {
        "a *-> b": Rule(
            [
                StateExpression([qre('a')], []),
                StateExpression([qre('b')], [])
            ],
            [
                MPLOperator('EVENT', 'CONSUME', 'STATE', 2)
            ]
        )
    }

    for result in collect_parsing_expectations(expectations, RuleExpressionParsers.expression):
        pass

