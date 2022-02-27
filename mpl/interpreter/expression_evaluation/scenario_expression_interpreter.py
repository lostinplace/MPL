from dataclasses import dataclass
from numbers import Number
from typing import Optional

from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.types import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.query_expression_interpreter import evaluate_symbolized_postfix_stack
from mpl.lib.query_logic import MPL_Context, FinalResultSet


@dataclass(frozen=True, order=True)
class ScenarioResult:
    value: FinalResultSet
    checkpoint: Optional[Reference] = None


    @staticmethod
    def calculate_weight(scenario: 'ScenarioResult'):
        sum_of_weights = 0
        for result in scenario.value:
            match result:
                case Number():
                    sum_of_weights += result
                case x:
                    sum_of_weights += 1
        return sum_of_weights

    @property
    def weight(self):
        return self.calculate_weight(self)


@dataclass(frozen=True, order=True)
class ScenarioExpressionInterpreter(ExpressionInterpreter):
    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: MPL_Context) -> ScenarioResult:
        value = evaluate_symbolized_postfix_stack(self.symbolized, context)

        return ScenarioResult(value)


