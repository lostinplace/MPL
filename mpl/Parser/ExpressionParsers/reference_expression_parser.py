
"""
# Reference Expression Parser

## Rules

Reference Expressions can be presented with or without parent types and any depth.  Parents can either be reserved words or other reference expressions

REFERENCE_EXPRESSION = REFERENCE_TOKEN (: REFERENCE_EXPRESSION)?
"""
import dataclasses
import re
import os
from numbers import Number

from sympy import Symbol
from dataclasses import dataclass
from typing import Optional, Tuple, Union, List, FrozenSet, Iterable

from parsita import TextParsers, opt, repsep, lit, longest
from parsita.util import splat

from mpl.Parser.Tokenizers.simple_value_tokenizer import SimpleValueTokenizers as svt, ReferenceToken


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
    types: FrozenSet[str] = frozenset()

    @staticmethod
    def ROOT():
        return Reference('ROOT')


    @property
    def types_str(self):
        match self.types:
            case str():
                return self.types
            case tuple() | frozenset():
                return ','.join(self.types)

        return ''

    @property
    def is_void(self) -> bool:
        return self.name == '*' or self.name[-2:] == '.*'

    @property
    def parent(self) -> 'Reference':
        tmp = self.to_reference_expression()
        new_lineage = tmp.path[:-1]
        parent_expr = ReferenceExpression(new_lineage, self.types)
        return parent_expr.reference

    @property
    def void(self) -> 'Reference':
        return dataclasses.replace(self, name=self.name + '.*')

    @property
    def expression(self) -> 'ReferenceExpression':
        return self.to_reference_expression()

    def to_reference_expression(self) -> 'ReferenceExpression':
        path = self.name.split('.')
        return ReferenceExpression(tuple(path), self.types)

    def __str__(self):
        types_str = self.types_str
        if types_str:
            return f'{self.name}: {types_str}'
        return self.name

    def __repr__(self):
        return f'Reference({self})'

    @property
    def symbol(self):
        return Symbol(self.name)

    @staticmethod
    def decode(symbol:  Symbol) -> Union['Reference']:
        return Reference(str(symbol))

    @property
    def without_types(self) -> 'Reference':
        return dataclasses.replace(self, types=frozenset())

    def with_types(self, types: Union[str, Iterable[str]]) -> 'Reference':
        if isinstance(types, str):
            types = {types}
        return dataclasses.replace(self, types=frozenset(types))

    def is_child_of(self, other: 'Reference') -> bool:
        return self.name.startswith(other.name + '.')

    @property
    def id(self):
        return hash(self)

    def __add__(self, other):
        return self.symbol + other

    def __radd__(self, other):
        return self.symbol + other

    def __sub__(self, other):
        return self.symbol - other

    def __rsub__(self, other):
        return self.symbol - other

    def __mul__(self, other):
        return self.symbol * other

    def __rmul__(self, other):
        return self.symbol * other

    def __truediv__(self, other):
        return self.symbol / other

    def __rtruediv__(self, other):
        return self.symbol / other

    def __pow__(self, power, modulo=None):
        return self.symbol ** power

    def __rpow__(self, power, modulo=None):
        return self.symbol ** power

    def to_entity(self, value: Optional[FrozenSet | Number | str] = None) -> 'EntityValue':
        from mpl.interpreter.expression_evaluation.entity_value import EntityValue

        match value:
            case frozenset():
                return EntityValue(value)
            case None:
                return EntityValue(frozenset())
            case x:
                return EntityValue(frozenset({x}))



Ref = Reference


@dataclass(frozen=True, order=True)
class ReferenceExpression:
    path: Tuple[str, ...]
    types: FrozenSet[str] = frozenset()
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
        if path == [ReferenceToken('True')] and not types:
            return True
        new_types = frozenset(type.content for type in types[0]) if types else frozenset()
        new_path = tuple(pathitem.content for pathitem in path)
        return ReferenceExpression(new_path, new_types)

    @staticmethod
    def void(prefix) -> 'ReferenceExpression':
        if prefix:
            as_strings = tuple(x.content for x in prefix[0])
            return ReferenceExpression(as_strings + ('*',))
        return ReferenceExpression(('*',))

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


