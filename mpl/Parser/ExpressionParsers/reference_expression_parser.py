
"""
# Reference Expression Parser

## Rules

Reference Expressions can be presented with or without parent types and any depth.  Parents can either be reserved words or other reference expressions

REFERENCE_EXPRESSION = REFERENCE_TOKEN (: REFERENCE_EXPRESSION)?
"""
import re
import os

from sympy import Symbol, symbols
from dataclasses import dataclass
from typing import Optional, Tuple, Iterable, Union

from parsita import TextParsers, opt
from parsita.util import splat

from mpl.Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers as svt, ReferenceToken
from mpl.lib.parsers.repsep2 import repsep2


def to(target_type):
    def result_func(parser_output):
        return target_type(parser_output)
    return result_func


def sanitize_reference_name(name: str) -> str:
    return re.sub(r'\s', '\u2e31', name)

def unsanitize_reference_name(name: str) -> str:
    return re.sub('\u2e31', r' ', name)

this_pid = str(os.getpid())
pattern = rf"^REF_{this_pid}_(?P<refname>.+)"

ref_symbol_pattern = re.compile(pattern)


@dataclass(frozen=True, order=True)
class Reference:
    name: str
    type: Optional[str] = None

    def stringify(self):
        result = f'{self.name}'
        if self.type:
            result += f': {self.type}'
        return result

    def sanitize(self) -> 'Reference':
        return Reference(sanitize_reference_name(self.name), self.type)

    def as_symbol(self) -> Symbol:
        name = sanitize_reference_name(self.name)
        return symbols(f'REF_{this_pid}_{name}')

    @staticmethod
    def decode(symbol:  Symbol) -> Union['Reference', Symbol]:
        result = ref_symbol_pattern.match(str(symbol))
        if result:
            refname = result.groupdict()['refname']
            return Reference(unsanitize_reference_name(refname))
        return symbol

    @property
    def id(self):
        return hash(self)

    def __add__(self, other):
        return self.as_symbol() + other

    def __radd__(self, other):
        return self.as_symbol() + other

    def __sub__(self, other):
        return self.as_symbol() - other

    def __rsub__(self, other):
        return self.as_symbol() - other

    def __mul__(self, other):
        return self.as_symbol() * other

    def __rmul__(self, other):
        return self.as_symbol() * other

    def __truediv__(self, other):
        return self.as_symbol() / other

    def __rtruediv__(self, other):
        return self.as_symbol() / other

    def __pow__(self, power, modulo=None):
        return self.as_symbol() ** power

    def __rpow__(self, power, modulo=None):
        return self.as_symbol() ** power


Ref = Reference


@dataclass(frozen=True, order=True)
class DeclarationExpression:
    name: str
    type: str
    reference: Reference


@dataclass(frozen=True, order=True)
class ReferenceExpression:
    value: Reference
    lineage: Tuple[Reference]

    def __str__(self):
        if self.value.name == 'void':
            return '*'

        lineage_str = '.'.join(ref.name for ref in self.lineage)
        lineage_str = lineage_str + '.' if lineage_str else ''
        return f"{lineage_str}{self.value.stringify()}"


def to_reference(reference: ReferenceToken, type):
    if type:
        type_name = type[0].content
        return Reference(reference.content, type_name)
    return Reference(reference.content, None)


def to_declaration(ref: Reference):
    return DeclarationExpression(ref.name, ref.type, ref)


def interpret_reference_expression(results):
    if isinstance(results, Iterable):
        tmp = tuple(reversed(results))
        main_ref = tmp[0]
        lineage = tuple(tmp[1:])
        return ReferenceExpression(main_ref, lineage)
    else:
        return ReferenceExpression(results, tuple())


class ReferenceExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    type_reference = svt.reference_token

    simple_reference = svt.reference_token & opt(':' >> type_reference) > splat(to_reference)

    pathed_reference = '//' >> repsep2(simple_reference, '/', min=1)

    simple_expression = simple_reference > interpret_reference_expression

    pathed_expression = pathed_reference > interpret_reference_expression

    declaration_expression = simple_reference > to_declaration

    expression = pathed_expression | simple_expression
