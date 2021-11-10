
"""
# Reference Expression Parser

## Rules

Reference Expressions can be presented with or without parent types and any depth.  Parents can either be reserved words or other reference expressions

REFERENCE_EXPRESSION = REFERENCE_TOKEN (: REFERENCE_EXPRESSION)?
"""
from dataclasses import dataclass
from typing import Union, Optional, List

from parsita import TextParsers, fwd, opt, Success, repsep, longest
from parsita.util import splat

from Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers as svt, ReferenceToken, ReservedToken
from lib.custom_parsers import repsep2, debug


def to(target_type):
    def result_func(parser_output):
        return target_type(parser_output)
    return result_func


@dataclass(frozen=True, order=True)
class Reference:
    name: str
    type: Optional[Union[ReferenceToken, ReservedToken]]


@dataclass(frozen=True, order=True)
class ReferenceExpression:
    value: Reference
    lineage: List[Reference]


def to_reference_operation(reference: ReferenceToken, type):
    out_type = None
    if type:
        out_type = type[0]
    return Reference(reference.content, out_type)


def interpret_reference_expression(results):
    tmp = list(reversed(results))
    main_ref = tmp[0]
    lineage = tmp[1:]
    return ReferenceExpression(main_ref, lineage)


class ReferenceExpressionParsers(TextParsers):
    type_reference = longest(svt.reserved_token, svt.reference_token)

    reference_operation = svt.reference_token & opt(':' >> type_reference) > splat(to_reference_operation)

    expression = repsep2(reference_operation, '/', min=1) > interpret_reference_expression
