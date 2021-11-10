from dataclasses import dataclass
from typing import Union, List, Optional

from parsita import TextParsers, fwd, longest

from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, ReferenceExpressionParsers as lep
from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers as aep, \
    ArithmeticExpression
from Parser.Tokenizers.operator_tokenizers import StateOperator, LogicalOperatorParsers as lop, LogicalOperator
from lib.custom_parsers import repsep2, SeparatedList, debug


@dataclass(frozen=True, order=True)
class LogicalOperation:
    operand: Union[ReferenceExpression, 'LogicalExpression']
    operator: Optional[LogicalOperator]


@dataclass(frozen=True, order=True)
class LogicalExpression:
    operands: List[
        Union[ReferenceExpression, ArithmeticExpression, 'LogicalExpression']
    ]
    operators: List[
        LogicalOperator
    ]


def interpret_negated_expression(parser_result):
    operand = parser_result[1]
    operator = parser_result[0]
    result = LogicalExpression([operand], [operator])
    return result


def interpret_simple_expression(parser_results: SeparatedList):
    operands = parser_results
    operators = parser_results.separators

    result = LogicalExpression(operands, operators)
    return result


class LogicalExpressionParsers(TextParsers):
    simple_logical_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_logical_expression << ')'

    negated_expression = fwd()
    logical_expression_operand = longest(
        parenthesized_simple_expression, \
        negated_expression, \
        lep.expression, \
        aep.expression
    )

    negated_expression.define(
        lop.logical_negation & logical_expression_operand > interpret_negated_expression
    )

    simple_logical_expression.define(
        repsep2(logical_expression_operand, lop.operator, min=1) > interpret_simple_expression
    )

    expression = negated_expression | simple_logical_expression
