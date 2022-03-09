from dataclasses import dataclass

from parsita import TextParsers

from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpressionParsers as QEP
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression


@dataclass(frozen=True, order=True)
class ScenarioExpression:
    value: QueryExpression

    def __str__(self):
        return f'%{{{self.value}}}'


class ScenarioExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = '%{' >> QEP.expression << '}' > ScenarioExpression
