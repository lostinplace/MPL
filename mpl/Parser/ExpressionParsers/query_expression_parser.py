from __future__ import annotations

from dataclasses import dataclass
from typing import Union, Tuple

from parsita import TextParsers, fwd, longest, lit

from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as RefExP, Reference
from mpl.Parser.ExpressionParsers.text_expression_parser import TextExpressionParsers as TexExP, TextExpression
from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers as ArExP, \
    ArithmeticExpression
from mpl.Parser.Tokenizers.operator_tokenizers import QueryOperatorParsers as lop, QueryOperator, ArithmeticOperator
from mpl.lib.parsers.repsep2 import repsep2, SeparatedList
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpressionParsers as TrgExP


@dataclass(frozen=True, order=True)
class Negation:
    operand: Union['QueryExpression', 'ReferenceExpression', 'StateExpression']


@dataclass(frozen=True, order=True)
class QueryExpression:
    operands: Tuple[
        ReferenceExpression | ArithmeticExpression | 'QueryExpression' | Negation | TextExpression, ...
    ]
    operators: Tuple[
        QueryOperator | ArithmeticOperator, ...
    ]


def interpret_negation(negation: Negation) -> QueryExpression:
    return QueryExpression(
        (negation.operand,),
        (QueryOperator('!'),)
    )


def interpret_simple_expression(parser_results: SeparatedList):
    operands = tuple(parser_results.__iter__())
    operators = parser_results.separators

    result = QueryExpression(operands, operators)
    return result


def interpret_void_reference_expression(_):
    re = ReferenceExpression(Reference('void', None), ())
    return re


class QueryExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    simple_logical_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_logical_expression << ')'
    void_state_expression = lit('*') > interpret_void_reference_expression

    negated_expression = fwd()
    logical_expression_operand = longest(
        void_state_expression,
        parenthesized_simple_expression,
        negated_expression,
        RefExP.expression,
        ArExP.expression,
        TrgExP.expression,
        TexExP.expression,
    )

    negation = lop.logical_negation >> logical_expression_operand > Negation

    negated_expression.define(
        negation > interpret_negation
    )

    simple_logical_expression.define(
        repsep2(logical_expression_operand, lop.operator, min=1) > interpret_simple_expression
    )

    expression = longest(negated_expression, simple_logical_expression)
