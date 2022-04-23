import dataclasses
from dataclasses import dataclass
from typing import Union, FrozenSet

from sympy import Expr
from sympy.core.relational import Relational

from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.entity_value import EntityValue

from mpl.interpreter.expression_evaluation.interpreters.expression_interpreter import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.stack_management import evaluate_symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.types import ExpressionResult, symbolized_postfix_stack
from mpl.lib.context_tree.context_tree_implementation import ContextTree


@dataclasses.dataclass(frozen=True, order=True)
class QueryResult(ExpressionResult):
    value: EntityValue


@dataclass(frozen=True, order=True)
class QueryExpressionInterpreter(ExpressionInterpreter):

    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: ContextTree) -> QueryResult:
        result = evaluate_symbolized_postfix_stack(self.symbolized, context)
        return QueryResult(result)

    @staticmethod
    def get_references_from_qri_like(qri: Union['QueryExpressionInterpreter', 'TargetExpressionInterpreter']) \
            -> FrozenSet[Reference]:
        result = set()
        for symbol in qri.symbolized:
            match symbol:
                case Expr() | Relational():
                    symbols = {x for x in symbol.free_symbols if '`' not in str(x)}
                    decoded = {Reference.decode(symbol) for symbol in symbols}
                    result |= decoded

        return frozenset(result)

    @property
    def references(self) -> FrozenSet[Reference]:
        return QueryExpressionInterpreter.get_references_from_qri_like(self)

    def __str__(self):
        return f"QueryExpressionInterpreter({self.expression})"