from __future__ import annotations

from dataclasses import dataclass
from itertools import zip_longest
from numbers import Number
from typing import Union, Tuple, FrozenSet, List

from parsita import TextParsers, fwd, longest, Success, Parser, repsep

from mpl.Parser.ExpressionParsers import Expression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as RefExP
from mpl.Parser.ExpressionParsers.text_expression_parser import TextExpressionParsers as TexExP, TextExpression
from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers as ArExP, \
    ArithmeticExpression
from mpl.Parser.Tokenizers.operator_tokenizers import QueryOperatorParsers as lop, QueryOperator, ArithmeticOperator
from mpl.interpreter.expression_evaluation.operators import query_operations_dict
from mpl.lib.parsers.repsep2 import repsep2, SeparatedList
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpressionParsers as TrgExP, TriggerExpression


@dataclass(frozen=True, order=True)
class Negation:
    operand: Union['QueryExpression', 'ReferenceExpression']

    def __str__(self):
        return f'!{str(self.operand)}'

    @staticmethod
    def interpret(operand: Union['QueryExpression', 'ReferenceExpression']):
        return Negation(operand)


@dataclass(frozen=True, order=True)
class VectorExpression(Expression):

    expressions: Tuple[QueryExpression]

    def __str__(self):
        return f'%{{{self.value}}}'

    @staticmethod
    def interpret(values: List[str]) -> 'VectorExpression':
        exprs = tuple(values)
        return VectorExpression(exprs)

    @property
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        return frozenset().union(*(expr.reference_expressions for expr in self.expressions))

    def qualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'VectorExpression':
        new_expressions = tuple(expr.qualify(context, ignore_types) for expr in self.expressions)
        return VectorExpression(new_expressions)

    def unqualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'VectorExpression':
        new_expressions = tuple(expr.unqualify(context, ignore_types) for expr in self.expressions)
        return VectorExpression(new_expressions)

    @staticmethod
    def to_frozen_set(v) -> FrozenSet:
        return frozenset(VectorExpression.to_tuple(v))

    @staticmethod
    def to_tuple(v) -> Tuple[Number | str, ...]:
        from mpl.interpreter.expression_evaluation.stack_management import postfix

        # TODO: This only works for value-vectors
        result = []
        for expr in v.expressions:
            tmp = postfix(expr, query_operations_dict)
            result.append(tmp[0])

        return tuple(result)


@dataclass(frozen=True, order=True)
class QueryExpression(Expression):

    operands: Tuple[
        ReferenceExpression | ArithmeticExpression | 'QueryExpression' | TextExpression | TriggerExpression, ...
    ]
    operators: Tuple[
        QueryOperator | ArithmeticOperator, ...
    ]

    @property
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        result = set()
        for operand in self.operands:
            if operand is True:
                continue
            result |= operand.reference_expressions
        return frozenset(result)

    def __str__(self):
        result = ''
        if len(self.operators) == 1 and self.operators[0] == QueryOperator('!'):
            return f'!{self.operands[0]}'
        for operand, operator in zip_longest(self.operands, self.operators):
            result += str(operand)
            if operator:
                result += f' {operator} '
        return result

    def __repr__(self):
        return f'QueryExpression({self})'

    def qualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'QueryExpression':
        new_operands = tuple(x.qualify(context, ignore_types) for x in self.operands)
        return QueryExpression(new_operands, self.operators)

    def unqualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'QueryExpression':
        new_operands = tuple(x.unqualify(context, ignore_types) for x in self.operands)
        return QueryExpression(new_operands, self.operators)

    @staticmethod
    def interpret(parser_results: SeparatedList | Negation):
        match parser_results:
            case Negation(x):
                return QueryExpression(
                    (x,),
                    (QueryOperator('!'),)
                )
            case SeparatedList():
                operands = tuple(parser_results.__iter__())
                operators = parser_results.separators

                result = QueryExpression(operands, operators)
                return result

    @staticmethod
    def parse(text: str) -> QueryExpression:
        tmp = QueryExpressionParsers.expression.parse(text)
        assert isinstance(tmp, Success)
        return tmp.value


class QueryExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    simple_logical_expression = fwd()
    vector_expression = fwd()

    parenthesized_simple_expression = '(' >> simple_logical_expression << ')'

    negation = lop.logical_negation >> \
               longest(RefExP.expression, parenthesized_simple_expression, TrgExP.expression) > Negation

    negated_expression = negation > QueryExpression.interpret

    logical_expression_operand = longest(
        parenthesized_simple_expression,
        vector_expression,
        negated_expression,
        RefExP.expression,
        ArExP.expression,
        TrgExP.expression,
        TexExP.expression,
    )

    simple_logical_expression.define(
        repsep2(logical_expression_operand, lop.operator, min=1) > QueryExpression.interpret
    )

    expression = longest(negated_expression, simple_logical_expression)
    vector_expression_tmp = '{' >> repsep(expression, ',') << '}' > VectorExpression.interpret
    vector_expression.define(vector_expression_tmp)
    vector_as_frozen_set = expression > VectorExpression.to_frozen_set
    vector_as_tuple = expression > VectorExpression.to_tuple


class VectorExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = QueryExpressionParsers.vector_expression
    expression_as_frozen_set = expression > VectorExpression.to_frozen_set
