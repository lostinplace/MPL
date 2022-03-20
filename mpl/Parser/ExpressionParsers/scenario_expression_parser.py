from dataclasses import dataclass
from typing import Tuple, FrozenSet

from parsita import TextParsers

from mpl.Parser.ExpressionParsers import Expression, T
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpressionParsers as QEP
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.vector_expression_parser import VectorExpression, VectorExpressionParsers as VEP


@dataclass(frozen=True, order=True)
class ScenarioExpression(Expression):
    def unqualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> T:
        return ScenarioExpression(self.value.unqualify(context, ignore_types))

    value: QueryExpression

    def __str__(self):
        return f'%{{{self.value}}}'

    @property
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        return self.value.reference_expressions

    def qualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'ScenarioExpression':
        return ScenarioExpression(self.value.qualify(context, ignore_types))

    @staticmethod
    def interpret(value: VectorExpression) -> 'ScenarioExpression':
        expr = value.expressions[0]
        return ScenarioExpression(expr)


class ScenarioExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = '%' >> VEP.expression > ScenarioExpression.interpret
