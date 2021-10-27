from dataclasses import dataclass
from typing import Union, List

from parsita import TextParsers, fwd

from Parser.ExpressionParsers.label_expression_parser import LabelExpression, LabelExpressionParsers as lep
from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers as aep
from Parser.Tokenizers.operator_tokenizers import StateOperator, LogicalOperatorParsers as lop
from lib.CustomParsers import repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class LogicalOperation:
    operand: Union[LabelExpression, 'LogicalExpression']
    operator: StateOperator


@dataclass(frozen=True, order=True)
class LogicalExpression:
    operations: List[LogicalOperation]


def interpret_negated_expression(parser_result):
    operand = parser_result[1]
    operator = parser_result[0]
    operation = LogicalOperation(operand, operator)
    result = LogicalExpression([operation])
    return result


def interpret_simple_expression(parser_results: SeparatedList):
    operands = parser_results
    operators = parser_results.separators + [None]

    operations = [LogicalOperation(operand, operator) for operand, operator in zip(operands, operators)]
    result = LogicalExpression(operations)
    return result


class LogicalExpressionParsers(TextParsers):
    simple_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_expression << ')'

    negated_expression = fwd()
    expression_operand = parenthesized_simple_expression | negated_expression | lep.expression | aep.expression
    __tmp_negated_expression = lop.logical_not & expression_operand > interpret_negated_expression
    negated_expression.define(__tmp_negated_expression)

    __tmp_se = repsep2(expression_operand, lop.operator) > interpret_simple_expression

    simple_expression.define(__tmp_se)
    expression = negated_expression | simple_expression
