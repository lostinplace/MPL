from __future__ import annotations

import typing
from dataclasses import dataclass, replace
from typing import FrozenSet, Tuple

from parsita import TextParsers
from parsita.util import splat

from mpl.Parser.ExpressionParsers import Expression, T
from mpl.Parser.ExpressionParsers.query_expression_parser \
    import QueryExpression, QueryExpressionParsers as QExP
from mpl.Parser.ExpressionParsers.reference_expression_parser \
    import ReferenceExpression, ReferenceExpressionParsers as RefExP
from mpl.Parser.Tokenizers.operator_tokenizers import AssignmentOperator, AssignmentOperatorParsers as AsOpP


@dataclass(frozen=True, order=True)
class AssignmentExpression(Expression):

    lhs: ReferenceExpression
    rhs: QueryExpression
    operator: AssignmentOperator = AssignmentOperator("=")

    def __str__(self) -> str:
        return f"{self.lhs} {self.operator} {self.rhs}"

    @property
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        return self.lhs.reference_expressions | self.rhs.reference_expressions

    def qualify(self, context: typing.Tuple[str, ...], ignore_types: bool = False) -> 'AssignmentExpression':
        new_lhs = self.lhs.qualify(context, ignore_types)
        new_rhs = self.rhs.qualify(context, ignore_types)
        return replace(self, lhs=new_lhs, rhs=new_rhs)

    def unqualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> T:
        new_lhs = self.lhs.unqualify(context, ignore_types)
        new_rhs = self.rhs.unqualify(context, ignore_types)
        return replace(self, lhs=new_lhs, rhs=new_rhs)

    def requalify(self, old_context: Tuple[str, ...], new_context: Tuple[str, ...]) -> T:
        new_lhs = self.lhs.requalify(old_context, new_context)
        new_rhs = self.rhs.requalify(old_context, new_context)
        return replace(self, lhs=new_lhs, rhs=new_rhs)

    @staticmethod
    def interpret(lhs: ReferenceExpression, op: AssignmentOperator, rhs: QueryExpression) -> 'AssignmentExpression':
        return AssignmentExpression(lhs, rhs, op)


class AssignmentExpressionParsers(TextParsers, whitespace=r'[ \t]*'):

    expression = RefExP.expression & AsOpP.operator & QExP.expression > splat(AssignmentExpression.interpret)
