from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression, AssignmentExpressionParsers
from Parser.ExpressionParsers.label_expression_parser import LabelExpression
from Parser.Tokenizers.operator_tokenizers import AssignmentOperator
from Parser.Tokenizers.simple_value_tokenizer import LabelToken

from Tests import assert_parsing_expectations, qdae, qle, collect_parsing_expectations


def test_rule_expression_parsers():
    pass
    # expectations = {
    #     'Hurt ~@ Turns Wounded: INT += 1': RuleExpression(
    #         qle('a'),
    #         qdae(1),
    #         AssignmentOperator('=')
    #     ),
    # }
    # tmp = AssignmentExpressionParsers.expression.parse('a = 1')
    # pass
    # results = collect_parsing_expectations(expectations, AssignmentExpressionParsers.expression)
    # for actual, expected in results:
    #     assert actual == expected

