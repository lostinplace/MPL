import dataclasses
from dataclasses import dataclass
from typing import FrozenSet

from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.interpreters.expression_interpreter import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.interpreters.query_expression_interpreter import QueryExpressionInterpreter
from mpl.interpreter.expression_evaluation.operators import OperatorOperation, OperationType, query_operations_dict
from mpl.interpreter.expression_evaluation.stack_management import evaluate_symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.types import ExpressionResult, symbolized_postfix_stack
from mpl.lib.context_tree.context_tree_implementation import ContextTree
from mpl.lib.query_logic.target_operations import target_xor, target_and, target_or


@dataclasses.dataclass(frozen=True, order=True)
class TargetResult(ExpressionResult):
    value: EntityValue


target_operations = {
    '^': OperatorOperation('^', 4, OperationType.Logical, target_xor),
    '&': OperatorOperation('&', 3, OperationType.Logical, target_and),
    '|': OperatorOperation('|', 2, OperationType.Logical, target_or),
}
target_operations_dict = query_operations_dict | target_operations


@dataclass(frozen=True, order=True)
class TargetExpressionInterpreter(ExpressionInterpreter):

    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: ContextTree) -> TargetResult:
        result = evaluate_symbolized_postfix_stack(self.symbolized, context)
        return TargetResult(result)

    @property
    def references(self) -> FrozenSet[Reference]:
        return QueryExpressionInterpreter.get_references_from_qri_like(self)

    def __str__(self):
        return f"TargetExpressionInterpreter({self.expression})"