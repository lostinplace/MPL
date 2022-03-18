import dataclasses
from dataclasses import dataclass
from typing import Optional, List, Tuple, FrozenSet

from parsita import TextParsers, opt, repsep
from parsita.util import splat

from mpl.Parser.ExpressionParsers import Expression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as refxp, \
    Reference


@dataclass(frozen=True, order=True)
class TriggerExpression(Expression):
    name: ReferenceExpression
    source: Optional[ReferenceExpression] = None
    messages: Optional[Tuple[ReferenceExpression, ...]] = None

    def __str__(self):
        source_str = f"{self.source} " if self.source else ""
        message_str = f"{self.messages} " if self.messages else ""
        return f"{source_str}<{self.name}>{message_str}"

    def __repr__(self):
        return f"Trigger({self.name})"

    def qualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'TriggerExpression':
        new_source = self.source.qualify(context, ignore_types) if self.source else None
        new_messages = tuple(message.qualify(context, ignore_types) for message in self.messages) if self.messages else None
        return TriggerExpression(self.name, new_source, new_messages)

    @property
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        messages = self.messages or ()
        result = {self.name, self.source, *messages} - {None}
        return frozenset(result)

    @staticmethod
    def interpret(
        source_expression: List[ReferenceExpression] = None,
        name_expression: ReferenceExpression = None,
        messages: List[ReferenceExpression] = None
    ) -> 'TriggerExpression':
        source = source_expression[0] if source_expression else None
        messages = tuple(messages) if messages else None
        return TriggerExpression(name_expression, source=source, messages=messages)


class TriggerExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = opt(refxp.expression) & '<' >> refxp.expression << '>' & repsep(refxp.expression, ',') \
                 > splat(TriggerExpression.interpret)
