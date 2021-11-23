from __future__ import annotations

import typing
from dataclasses import dataclass, fields, replace

from parsita import TextParsers, longest

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression, ArithmeticExpressionParsers as aep
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, LogicalExpressionParsers as LoExP
from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, ReferenceExpressionParsers as lep
from Parser.Tokenizers.operator_tokenizers import AssignmentOperator, AssignmentOperatorParsers as aop


@dataclass(frozen=True, order=True)
class AssignmentExpression:
    lhs: ReferenceExpression
    rhs: ArithmeticExpression | LogicalExpression
    operator: AssignmentOperator


default_assignment_expression = AssignmentExpression(None, None, None)


def interpret_to(default_dataclass, keys: typing.List[str]):
    def interpret_parser_results(parser_results):
        replacements = dict()
        for index, value in enumerate(parser_results):
            replacements[keys[index]] = value
        result = replace(default_dataclass, **replacements)
        return result
    return interpret_parser_results


class AssignmentExpressionParsers(TextParsers, whitespace=r'[ \t]*'):

    expression = lep.expression & aop.operator & longest(aep.expression, LoExP.expression) > \
                 interpret_to(default_assignment_expression, ['lhs', 'operator', 'rhs'])
