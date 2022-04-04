from __future__ import annotations

import dataclasses
from typing import Dict, FrozenSet, Tuple


from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.interpreters.expression_interpreter import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.stack_management import evaluate_symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack
from mpl.lib.context_tree.context_tree_implementation import ContextTree


@dataclasses.dataclass(frozen=True, order=True)
class AssignmentResult:
    value: EntityValue
    change: Dict[Reference, EntityValue]


@dataclasses.dataclass(frozen=True, order=True)
class AssignmentExpressionInterpreter(ExpressionInterpreter):
    expression: AssignmentExpression
    reference: Reference
    symbolized: symbolized_postfix_stack

    def interpret(self, context: EngineContext) -> AssignmentResult:
        target_value = evaluate_symbolized_postfix_stack(self.symbolized, context)
        _, diff = context.set(self.reference, target_value)
        change = {k: v[1] for k, v in diff.items() if v is not None}
        return AssignmentResult(target_value, change)

    @property
    def references(self) -> FrozenSet[Reference]:
        result = {self.reference} | self.expression.references
        return frozenset(result)

    def __str__(self):
        return f"AssignmentExpressionInterpreter({self.expression})"


def evaluate_assignment_expression(
        reference: Reference,
        symbolized_stack: symbolized_postfix_stack,
        context: ContextTree
) -> Tuple[Reference, EntityValue]:
    from mpl.interpreter.expression_evaluation.entity_value import EntityValue

    increment_value = evaluate_symbolized_postfix_stack(symbolized_stack, context)
    iv = EntityValue.from_value(increment_value)
    existing_value = context[reference]
    match existing_value:
        case EntityValue():
            new_value = dataclasses.replace(existing_value, value=iv)
        case _:
            new_value = iv

    return reference, new_value