from dataclasses import dataclass
from typing import Union, List

from parsita import TextParsers, fwd, longest

from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, ReferenceExpressionParsers as lexp
from Parser.Tokenizers.operator_tokenizers import ArithmeticOperator, ArithmeticOperatorParsers as aop
from Parser.Tokenizers.simple_value_tokenizer import NumberToken, SimpleValueTokenizers as svt
from lib.repsep2 import repsep2


@dataclass(frozen=True, order=True)
class ArithmeticOperation:
    operand: Union[NumberToken, ReferenceExpression, 'ArithmeticExpression']
    operator: ArithmeticOperator


@dataclass(frozen=True, order=True)
class ArithmeticExpression:
    operands: List[Union[NumberToken, ReferenceExpression, 'ArithmeticExpression']]
    operators: List[ArithmeticOperator]


def interpret_simple_expression(parser_results):
    operands = parser_results
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
