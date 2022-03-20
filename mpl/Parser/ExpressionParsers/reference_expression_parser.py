
"""
# Reference Expression Parser

## Rules

Reference Expressions can be presented with or without parent types and any depth.  Parents can either be reserved words or other reference expressions

REFERENCE_EXPRESSION = REFERENCE_TOKEN (: REFERENCE_EXPRESSION)?
"""
import dataclasses
import re
import os

from sympy import Symbol, symbols
from dataclasses import dataclass
from typing import Optional, Tuple, Iterable, Union, List, FrozenSet, Dict

from parsita import TextParsers, opt, repsep, Success, lit, longest
from parsita.util import splat

from mpl.Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers as svt, ReferenceToken
from mpl.lib import fs


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
    types: Optional[FrozenSet[str]] = None

    def stringify(self):
        result = f'{self.name}'
        if self.types:
            result += f': {self.types}'
        return result

    @property
    def types_str(self):
        match self.types:
            case str():
                return self.types
            case tuple() | frozenset():
                return ','.join(self.types)
            case None:
                return ''
            case _:
                return ''

    def to_reference_expression(self) -> 'ReferenceExpression':
        path = self.name.split('.')
        return ReferenceExpression(tuple(path), self.types)

    @property
    def as_type_dict(self) -> Dict[str, 'Reference']:
        result = {None: dataclasses.replace(self, types=None)}
        if self.types:
            for t in self.types:
                result[t] = dataclasses.replace(self, types=frozenset({t}))
        return result

    def __str__(self):
        types_str = self.types_str
        if types_str:
            return f'{self.name}: {types_str}'
        return self.name

    def __repr__(self):
        return f'Reference({self})'

    def sanitize(self) -> 'Reference':
        return Reference(sanitize_reference_name(self.name), self.types)

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
    def without_types(self) -> 'Reference':
        return dataclasses.replace(self, types=None)

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
class ReferenceExpression:
    path: Tuple[str, ...]
    types: Optional[FrozenSet[str]] = None
    parent: Optional['ReferenceExpression'] = None

    @property
    def reference(self) -> Reference:
        name = '.'.join(self.path)
        return Reference(name, self.types)

    def __str__(self):
        result = ''
        if self.path[-1:] == ('void',):
            result = '.'.join(self.path[:-1] + ('*',))
        else:
            result = str(self.reference)
        if self.parent:
            result = f'{result} in {self.parent}'
        return result

    def __repr__(self):
        return f"ReferenceExpression({self})"

    @staticmethod
    def interpret(path: List[ReferenceToken], types: List[List[ReferenceToken]]) -> 'ReferenceExpression':
        new_types = frozenset(type.content for type in types[0]) if types else None
        new_path = tuple(pathitem.content for pathitem in path)
        return ReferenceExpression(new_path, new_types)

    @staticmethod
    def void(prefix) -> 'ReferenceExpression':
        if prefix:
            as_strings = tuple(x.content for x in prefix[0])
            return ReferenceExpression(as_strings + ('void',), None)
        return ReferenceExpression(('void',))

    def qualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'ReferenceExpression':
        return ReferenceExpression(context + self.path, self.types if not ignore_types else frozenset())

    def unqualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'ReferenceExpression':
        if self.path[:len(context)] == context:
            return ReferenceExpression(self.path[len(context):], self.types if not ignore_types else frozenset())
        return self

    @property
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        return frozenset({self})




class ReferenceExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    type_reference = lit(':') >> repsep(svt.reference_token, ',', min=1)

    void_expression = opt(repsep(svt.reference_token, '.', min=1) << '.') << lit('*') > ReferenceExpression.void

    reference_expression = repsep(svt.reference_token, '.', min=1) & opt(type_reference) \
                           > splat(ReferenceExpression.interpret)

    expression = longest(void_expression, reference_expression)


def test_reference_expression_parsing():

    expectations = {
        'test me': Reference('test me', None),
        'base.test me': Reference('base.test me', None),
        'base.test me:int': Reference('base.test me', fs('int')),
    }

    for input, expected in expectations.items():
        result = ReferenceExpressionParsers.expression.parse(input)
        assert isinstance(result, Success)
        expression = result.value
        actual = expression.reference
        assert actual == expected, input
