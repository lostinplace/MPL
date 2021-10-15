import typing
from dataclasses import dataclass, fields, replace

from parsita import TextParsers

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression, ArithmeticExpressionParsers as aep
from Parser.ExpressionParsers.label_expression_parser import LabelExpression, LabelExpressionParsers as lep
from Parser.Tokenizers.operator_tokenizers import AssignmentOperator, AssignmentOperatorParsers as aop

# TODO: Have to do State Expression parser first
#
# @dataclass(frozen=True, order=True)
# class RuleOperation:
#     operand: Union[AssignmentExpression, ArithmeticExpression]
#
# @dataclass(frozen=True, order=True)
# class RuleExpression:
#     operations: List[RuleOperation]
#
#
# default_assignment_expression = AssignmentExpression(None, None, None)
#
#
# def interpret_to(default_dataclass, keys: typing.List[str]):
#     def interpret_parser_results(parser_results):
#         replacements = dict()
#         for index, value in enumerate(parser_results):
#             replacements[keys[index]] = value
#         result = replace(default_dataclass, **replacements)
#         return result
#     return interpret_parser_results
#
#
# class AssignmentExpressionParsers(TextParsers):
#
#     expression = lep.expression & aop.operator & aep.expression > \
#                  interpret_to(default_assignment_expression, ['lhs', 'operator', 'rhs'])
