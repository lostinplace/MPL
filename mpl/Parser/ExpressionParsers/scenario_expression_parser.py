from dataclasses import dataclass
from typing import Tuple, FrozenSet

from parsita import TextParsers

from mpl.Parser.ExpressionParsers import Expression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpressionParsers as QEP
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression


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


class ScenarioExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = '%{' >> QEP.expression << '}' > ScenarioExpression
