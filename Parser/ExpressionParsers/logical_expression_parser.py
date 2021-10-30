from dataclasses import dataclass
from typing import Union, List, Optional

from parsita import TextParsers, fwd, longest

from Parser.ExpressionParsers.label_expression_parser import LabelExpression, LabelExpressionParsers as lep
from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers as aep
from Parser.Tokenizers.operator_tokenizers import StateOperator, LogicalOperatorParsers as lop, LogicalOperator
from lib.CustomParsers import repsep2, SeparatedList, debug


@dataclass(frozen=True, order=True)
class LogicalOperation:
    operand: Union[LabelExpression, 'LogicalExpression']
    operator: Optional[LogicalOperator]


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


def db_cb(parser, reader):
    pass


class LogicalExpressionParsers(TextParsers):
    simple_logical_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_logical_expression << ')'

    negated_expression = fwd()
    logical_expression_operand = longest(
        debug(parenthesized_simple_expression, callback=db_cb), \
        negated_expression, \
        lep.expression, \
        debug(aep.expression, callback=db_cb)
    )

    negated_expression.define(
        lop.logical_negation & logical_expression_operand > interpret_negated_expression
    )

    simple_logical_expression.define(
        debug(repsep2(logical_expression_operand, lop.operator, min=1), callback=db_cb) > interpret_simple_expression
    )

    expression = negated_expression | simple_logical_expression
