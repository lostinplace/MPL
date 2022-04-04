import dataclasses
from numbers import Number
from typing import Optional, FrozenSet

from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.interpreters.expression_interpreter import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.stack_management import evaluate_symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack
from mpl.lib.context_tree.context_tree_implementation import ContextTree


@dataclasses.dataclass(frozen=True, order=True)
class ScenarioResult:
    value: EntityValue
    checkpoint: Optional[Reference] = None

    @staticmethod
    def calculate_weight(scenario: 'ScenarioResult'):
        sum_of_weights = 0
        for result in scenario.value.value:
            match result:
                case Number():
                    sum_of_weights += result
                case _:
                    sum_of_weights += 1
        return sum_of_weights

    @property
    def weight(self):
        return self.calculate_weight(self)


@dataclasses.dataclass(frozen=True, order=True)
class ScenarioExpressionInterpreter(ExpressionInterpreter):
    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: ContextTree) -> ScenarioResult:
        value = evaluate_symbolized_postfix_stack(self.symbolized, context)
        return ScenarioResult(value)

    @property
    def references(self) -> FrozenSet[Reference]:
        return self.expression.references

    def __str__(self):
        return f"ScenarioExpressionInterpreter({self.expression})"