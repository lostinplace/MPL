from __future__ import annotations

from dataclasses import dataclass
from itertools import zip_longest
from typing import Union, Tuple

from parsita import TextParsers, fwd, longest

from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, ReferenceExpressionParsers as lexp
from mpl.Parser.Tokenizers.operator_tokenizers import ArithmeticOperator, ArithmeticOperatorParsers as aop
from mpl.Parser.Tokenizers.simple_value_tokenizer import NumberToken, SimpleValueTokenizers as svt
from mpl.lib.parsers.repsep2 import repsep2


@dataclass(frozen=True, order=True)
class ArithmeticOperation:
    operand: Union[NumberToken, ReferenceExpression, 'ArithmeticExpression']
    operator: ArithmeticOperator


@dataclass(frozen=True, order=True)
class ArithmeticExpression:
    operands: Tuple[NumberToken | ReferenceExpression | 'ArithmeticExpression']
    operators: Tuple[ArithmeticOperator]

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


def interpret_simple_expression(parser_results):
    operands = tuple(parser_results)
    operators = parser_results.separators

    result = ArithmeticExpression(operands, operators)
    return result


class ArithmeticExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    simple_arithmetic_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_arithmetic_expression << ')'

    arithmetic_expression_operand = parenthesized_simple_expression | lexp.expression | svt.number_token
    __tmp_se = repsep2(arithmetic_expression_operand, aop.operator, min=1) > interpret_simple_expression
    simple_arithmetic_expression.define(__tmp_se)

    expression = longest(parenthesized_simple_expression, simple_arithmetic_expression)
