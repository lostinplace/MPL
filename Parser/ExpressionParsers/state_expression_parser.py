from __future__ import annotations

from dataclasses import dataclass
from typing import Union, List, Tuple

from parsita import TextParsers, fwd, opt, lit, longest

from Parser.ExpressionParsers.logical_expression_parser import Negation
from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression,\
    ReferenceExpressionParsers as refxp,  Reference
from Parser.ExpressionParsers.trigger_expression_parser import TriggerExpressionParsers as texp
from Parser.Tokenizers.operator_tokenizers import StateOperator, StateOperatorParsers as sop, iw
from lib.repsep2 import repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class StateOperation:
    operand: Union[ReferenceExpression, 'StateExpression']
    operator: StateOperator


@dataclass(frozen=True, order=True)
class StateExpression:
    operands: Tuple[ReferenceExpression | 'StateExpression' | Negation]
    operators: Tuple[StateOperator]


def interpret_negated_expression(parser_result):
    result = Negation(parser_result)
    return result


def interpret_state_expression(parser_results: SeparatedList):
    if len(parser_results) == 1 and isinstance(parser_results[0], StateExpression):
        return parser_results[0]

    operands = tuple(parser_results.__iter__())
    operators = parser_results.separators

    result = StateExpression(operands, operators)
    return result


def interpret_void_state_expression(_):
    re = ReferenceExpression(Reference('void', None), ())
    return StateExpression(
        (re,),
        ()
    )


class StateExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = fwd()
    parenthesized_expression = '(' >> expression << ')'
    void_state_expression = lit('*') > interpret_void_state_expression
    negated_expression = fwd()

    negated_expression.define(
        iw >> sop.not_state >> \
        longest(
            void_state_expression,
            parenthesized_expression,
            texp.expression,
            refxp.expression
        ) << iw > Negation

    )

    simple_expression_operand = longest(
            void_state_expression,
            parenthesized_expression,
            negated_expression,
            texp.expression,
            refxp.expression
        )

    repeated_expression_operations = repsep2(
        simple_expression_operand,
        (sop.and_state | sop.or_state),
        min=1
    ) > interpret_state_expression

    expression.define(repeated_expression_operations)
