from dataclasses import dataclass

from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.interpreter.expression_evaluation.types import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.query_expression_interpreter import evaluate_symbolized_postfix_stack
from mpl.lib.query_logic import MPL_Context, FinalResultSet


@dataclass(frozen=True, order=True)
class ScenarioResult:
    value: FinalResultSet


@dataclass(frozen=True, order=True)
class ScenarioExpressionInterpreter(ExpressionInterpreter):
    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: MPL_Context) -> ScenarioResult:
        value = evaluate_symbolized_postfix_stack(self.symbolized, context)

        return ScenarioResult(value)


