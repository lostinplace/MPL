from dataclasses import dataclass
from typing import Tuple, FrozenSet

from parsita import TextParsers

from mpl.Parser.ExpressionParsers import Expression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression, VectorExpression, \
    VectorExpressionParsers as VEP


@dataclass(frozen=True, order=True)
class ScenarioExpression(Expression):

    value: QueryExpression

    def __str__(self):
        return f'%{{{self.value}}}'

    @property
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        return self.value.reference_expressions

    def qualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'ScenarioExpression':
        return ScenarioExpression(self.value.qualify(context, ignore_types))

    def unqualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'ScenarioExpression':
        return ScenarioExpression(self.value.unqualify(context, ignore_types))

    def requalify(self, old_context: Tuple[str, ...], new_context: Tuple[str, ...]) -> 'ScenarioExpression':
        return ScenarioExpression(self.value.requalify(old_context, new_context))

    @staticmethod
    def interpret(value: VectorExpression) -> 'ScenarioExpression':
        expr = value.expressions[0]
        return ScenarioExpression(expr)


class ScenarioExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = '%' >> VEP.expression > ScenarioExpression.interpret
