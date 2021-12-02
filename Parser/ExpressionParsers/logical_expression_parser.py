from __future__ import annotations

from dataclasses import dataclass
from typing import Union, List, Optional, Tuple

from parsita import TextParsers, fwd, longest

from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as RefExP
from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers as ArExP, \
    ArithmeticExpression
from Parser.Tokenizers.operator_tokenizers import LogicalOperatorParsers as lop, LogicalOperator
from lib.repsep2 import repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class Negation:
    operand: Union['LogicalExpression', 'ReferenceExpression', 'StateExpression']


@dataclass(frozen=True, order=True)
class LogicalExpression:
    operands: Tuple[
        ReferenceExpression | ArithmeticExpression | 'LogicalExpression' | Negation
    ]
    operators: Tuple[
        LogicalOperator
    ]


def interpret_negated_expression(parser_result):
    operand = parser_result
    result = Negation(operand)
    return result


def interpret_simple_expression(parser_results: SeparatedList):
    operands = tuple(parser_results.__iter__())
    operators = parser_results.separators

    result = LogicalExpression(operands, operators)
    return result


class LogicalExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    simple_logical_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_logical_expression << ')'

    negated_expression = fwd()
    logical_expression_operand = longest(
        parenthesized_simple_expression, \
        negated_expression, \
        RefExP.expression, \
        ArExP.expression
    )

    negated_expression.define(
        lop.logical_negation >> logical_expression_operand > Negation
    )

    simple_logical_expression.define(
        repsep2(logical_expression_operand, lop.operator, min=1) > interpret_simple_expression
    )

    expression = negated_expression | simple_logical_expression
