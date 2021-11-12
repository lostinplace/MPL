
"""
# Reference Expression Parser

## Rules

Reference Expressions can be presented with or without parent types and any depth.  Parents can either be reserved words or other reference expressions

REFERENCE_EXPRESSION = REFERENCE_TOKEN (: REFERENCE_EXPRESSION)?
"""
from dataclasses import dataclass
from typing import Union, Optional, List

from parsita import TextParsers, opt, longest, lit
from parsita.util import splat

from Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers as svt, ReferenceToken
from lib.custom_parsers import debug
from lib.repsep2 import repsep2


def to(target_type):
    def result_func(parser_output):
        return target_type(parser_output)
    return result_func


@dataclass(frozen=True, order=True)
class Reference:
    name: str
    type: Optional[str]


@dataclass(frozen=True, order=True)
class DeclarationExpression:
    name: str
    type: str
    reference: Reference


@dataclass(frozen=True, order=True)
class ReferenceExpression:
    value: Reference
    lineage: List[Reference]


def to_reference(reference: ReferenceToken, type):
    if type:
        type_name = type[0].content
        return Reference(reference.content, type_name)
    return Reference(reference.content, None)


def to_declaration(ref: Reference):
    return DeclarationExpression(ref.name, ref.type, ref)


def interpret_reference_expression(results):
    if isinstance(results, list):
        tmp = list(reversed(results))
        main_ref = tmp[0]
        lineage = tmp[1:]
        return ReferenceExpression(main_ref, lineage)
    else:
        return ReferenceExpression(results, [])


class ReferenceExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    type_reference = svt.reference_token

    simple_reference = svt.reference_token & opt(':' >> type_reference) > splat(to_reference)

    pathed_reference = '//' >> repsep2(simple_reference, '/', min=1)

    simple_expression = simple_reference > interpret_reference_expression

    pathed_expression = pathed_reference > interpret_reference_expression

    declaration_expression = simple_reference > to_declaration

    expression = pathed_expression | simple_expression
