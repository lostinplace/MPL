import dataclasses
from dataclasses import dataclass
from typing import Optional

from parsita import TextParsers, fwd, opt, lit
from parsita.util import splat

from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as refxp, \
    Reference, interpret_reference_expression
from lib.custom_parsers import debug


@dataclass(frozen=True, order=True)
class TriggerExpression:
    name: Reference
    message: Optional[ReferenceExpression]


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
