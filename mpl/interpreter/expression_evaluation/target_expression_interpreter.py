from dataclasses import dataclass
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.interpreter.expression_evaluation.query_expression_interpreter import evaluate_symbolized_postfix_stack

from mpl.interpreter.expression_evaluation.types import ExpressionInterpreter, ExpressionResult
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack
from mpl.interpreter.expression_evaluation.operators import OperationType, OperatorOperation, query_operations_dict
from mpl.lib.query_logic import MPL_Context, FinalResultSet, target_xor, target_and, target_or


@dataclass(frozen=True, order=True)
class TargetResult(ExpressionResult):
    value: FinalResultSet


target_operations = {
    '^': OperatorOperation('^', 4, OperationType.Logical, target_xor),  # done
    '&': OperatorOperation('&', 3, OperationType.Logical, target_and),  # done
    '|': OperatorOperation('|', 2, OperationType.Logical, target_or),  # done
}

target_operations_dict = query_operations_dict | target_operations


@dataclass(frozen=True, order=True)
class TargetExpressionInterpreter(ExpressionInterpreter):
    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: MPL_Context) -> TargetResult:
        result = evaluate_symbolized_postfix_stack(self.symbolized, context, True)
        return TargetResult(result)