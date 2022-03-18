from __future__ import annotations

from dataclasses import dataclass
from itertools import zip_longest
from typing import Union, Tuple, FrozenSet

from parsita import TextParsers, fwd, longest

from mpl.Parser.ExpressionParsers import Expression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as RefExP
from mpl.Parser.Tokenizers.operator_tokenizers import ArithmeticOperator, ArithmeticOperatorParsers as aop
from mpl.Parser.Tokenizers.simple_value_tokenizer import NumberToken, SimpleValueTokenizers as svt
from mpl.lib.parsers.repsep2 import repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class ArithmeticOperation:
    operand: Union[NumberToken, ReferenceExpression, 'ArithmeticExpression']
    operator: ArithmeticOperator


@dataclass(frozen=True, order=True)
class ArithmeticExpression(Expression):

    operands: Tuple[NumberToken | ReferenceExpression | 'ArithmeticExpression', ...]
    operators: Tuple[ArithmeticOperator, ...]

    @property
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        result = frozenset()
        for operand in self.operands:
            match operand:
                case ArithmeticExpression() | ReferenceExpression():
                    result |= operand.reference_expressions
                case _:
                    pass
        return result

    def __str__(self):
        result = ''
        for operand, operator in zip_longest(self.operands, self.operators):
            match operand:
                case ArithmeticExpression():
                    result += f'({operand})'
                case _:
                    result += str(operand)
            if operator is not None:
                result += str(operator)
        return result

    def qualify(self, context: Tuple[str, ...], ignore_types:bool = False) -> 'ArithmeticExpression':
        new_operands = tuple(
            operand.qualify(context, ignore_types)
            if isinstance(operand, (ReferenceExpression, ArithmeticExpression)) else operand
            for operand in self.operands
        )
        return ArithmeticExpression(new_operands, self.operators)

    @staticmethod
    def interpret(parser_results: SeparatedList) -> 'ArithmeticExpression':
        operands = tuple(parser_results)
        operators = parser_results.separators

        result = ArithmeticExpression(operands, operators)
        return result


class ArithmeticExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    simple_arithmetic_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_arithmetic_expression << ')'

    arithmetic_expression_operand = parenthesized_simple_expression | RefExP.expression | svt.number_token
    __tmp_se = repsep2(arithmetic_expression_operand, aop.operator, min=1) > ArithmeticExpression.interpret
    simple_arithmetic_expression.define(__tmp_se)

    expression = longest(parenthesized_simple_expression, simple_arithmetic_expression)
