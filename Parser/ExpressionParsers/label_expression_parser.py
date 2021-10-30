
"""
# Label Expression Parser

## Rules

Label Expressions can be presented with or without parent types and any depth.  Parents can either be reserved words or other label expressions

LABEL_EXPRESSION = LABEL_TOKEN (: LABEL_EXPRESSION)?
"""
from dataclasses import dataclass
from typing import Union

from parsita import TextParsers, fwd, opt, Success
from parsita.util import splat

from Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers, LabelToken, ReservedToken
from lib.CustomParsers import track


def to(target_type):
    def result_func(parser_output):
        return target_type(parser_output)
    return result_func


@dataclass(frozen=True, order=True)
class LabelExpression:
    name: str
    depth: int
    token: Union[LabelToken, ReservedToken]
    parent: 'LabelExpression'


def interpret_label_expression(parser_result):
    """TODO: Reserved Tokens don't work right here"""
    (token, parent) = parser_result.value

    tmp = SimpleValueTokenizers.reserved_token.parse(token.content)
    if isinstance(tmp, Success):
        token = tmp.value

    parent = parent and parent[0] or None
    name = token.content.strip()
    result = LabelExpression(name, parser_result.start, token, parent)
    return result


class LabelExpressionParsers(TextParsers):
    """TODO: Reserved Tokens don't work right here"""
    expression = fwd()
    _tmp = track((SimpleValueTokenizers.label_token) & opt(':' >> expression)) > interpret_label_expression
    expression.define(_tmp)