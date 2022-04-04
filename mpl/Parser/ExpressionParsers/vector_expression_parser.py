from dataclasses import dataclass
from numbers import Number
from typing import Tuple, FrozenSet, List

from parsita import TextParsers, repsep

from mpl.Parser.ExpressionParsers import Expression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpressionParsers as QEP
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.interpreter.expression_evaluation.operators import query_operations_dict


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


class VectorExpressionParsers(TextParsers, whitespace=r'[ \t]*'):
    expression = '{' >> repsep(QEP.expression, ',') << '}' > VectorExpression.interpret
    vector_as_frozen_set = expression > VectorExpression.to_frozen_set
    vector_as_tuple = expression > VectorExpression.to_tuple
