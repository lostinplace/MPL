from dataclasses import dataclass

from parsita import TextParsers

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression, \
    ArithmeticExpressionParsers as AExp


@dataclass(frozen=True, order=True)
class ScenarioExpression:
    value: ArithmeticExpression


class ScenarioExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = '%{' >> AExp.expression << '}' > ScenarioExpression
