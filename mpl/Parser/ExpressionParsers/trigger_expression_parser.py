import dataclasses
from dataclasses import dataclass
from typing import Optional

from parsita import TextParsers, opt
from parsita.util import splat

from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as refxp, \
    Reference


@dataclass(frozen=True, order=True)
class TriggerExpression:
    name: Reference
    message: Optional[ReferenceExpression]

    def __str__(self):
        message_str =''
        if self.message:
            message_str = f' ({self.message})'
        return f"<{self.name.name}>{message_str}"


def interpret_expression(name:ReferenceExpression, message):
    name_ref = dataclasses.replace(name.value, type='trigger')
    if message:
        message = message[0]
    else:
        message = None
    result = TriggerExpression(name_ref, message)
    return result


class TriggerExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = '<' >> refxp.simple_expression << '>' & opt(refxp.simple_expression) > splat(interpret_expression)
