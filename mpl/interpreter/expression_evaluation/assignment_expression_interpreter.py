import dataclasses
import itertools
from dataclasses import dataclass
from typing import Tuple

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.types import ExpressionInterpreter, ChangeLedgerRef
from mpl.interpreter.expression_evaluation.query_expression_interpreter import symbolized_postfix_stack, \
    evaluate_symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.operators import OperationType, OperatorOperation
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity
from mpl.lib.query_logic import MPL_Context, FinalResultSet


def evaluate_assignment_expression(
        reference: Reference,
        symbolized_stack: symbolized_postfix_stack,
        context: MPL_Context
) -> Tuple[Reference, FinalResultSet]:

    increment_value = evaluate_symbolized_postfix_stack(symbolized_stack, context)
    existing_value = context[reference]
    match existing_value:
        case MPLEntity():
            new_value = dataclasses.replace(existing_value, value=increment_value)
        case _:
            new_value = increment_value

    return reference, new_value


@dataclass(frozen=True, order=True)
class AssignmentResult:
    value: MPL_Context


@dataclass(frozen=True, order=True)
class AssignmentExpressionInterpreter(ExpressionInterpreter):
    expression: AssignmentExpression
    reference: Reference
    operator: OperatorOperation
    symbolized: symbolized_postfix_stack

    def interpret(self, context: MPL_Context) -> AssignmentResult:
        change = evaluate_assignment_expression(self.reference, self.symbolized, context)
        existing_changes = context.get(ChangeLedgerRef) or dict()
        change = {change[0]: change[1]}
        update = {ChangeLedgerRef: existing_changes | change}
        result = context | change | update
        return AssignmentResult(value=result)
