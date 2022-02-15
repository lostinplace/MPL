from dataclasses import dataclass
from typing import Union

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.Parser.Tokenizers.operator_tokenizers import QueryOperator
from mpl.interpreter.expression_evaluation.operators import OperatorOperation, op_dict, OperationType
from mpl.interpreter.expression_evaluation.query_expression_interpreter import symbolized_postfix_stack, symbolize_expression
from mpl.interpreter.expression_evaluation.assignmment_expression_interpreter import evaluate_assignment_expression
from mpl.interpreter.expression_evaluation.query_expression_interpreter import symbolized_postfix_stack, \
    evaluate_symbolized_postfix_stack, symbolize_expression
from mpl.lib.logic import MPL_Context


latest_entry_ref = Reference("{}")


@dataclass(frozen=True, order=True)
class QueryExpressionInterpreter:
    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def evaluate(self, context: MPL_Context) -> MPL_Context:
        result = evaluate_symbolized_postfix_stack(self.symbolized, context)
        return {latest_entry_ref: (result,)}


@dataclass(frozen=True, order=True)
class AssignmentExpressionInterpreter:
    expression: AssignmentExpression
    reference: Reference
    operator: OperatorOperation
    symbolized: symbolized_postfix_stack

    def evaluate(self, context: MPL_Context) -> MPL_Context:
        result = evaluate_assignment_expression(self.reference, self.operator, self.symbolized, context)
        return result


@dataclass(frozen=True, order=True)
class ScenarioExpressionInterpreter:
    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def evaluate(self, context: MPL_Context) -> MPL_Context:
        scenario_value = evaluate_symbolized_postfix_stack(self.symbolized, context)
        return {Ref('%'): (scenario_value,)}


assignment_operator = op_dict['=']


def create_interpreter(expression: Union[QueryExpression, AssignmentExpression]) -> QueryExpressionInterpreter:
    match expression:
        case QueryExpression():
            stack = symbolize_expression(expression)
            return QueryExpressionInterpreter(expression, stack)
        case ScenarioExpression() as x:
            stack = symbolize_expression(expression.value)
            return ScenarioExpressionInterpreter(expression, stack)
        case AssignmentExpression():
            operator = op_dict[expression.operator.contents]
            reference = expression.lhs.value
            match operator.operation_type:
                case OperationType.Assign:
                    stack = symbolize_expression(expression.rhs)
                    return AssignmentExpressionInterpreter(expression, reference, operator, stack)
                case OperationType.Increment:
                    normal_sign = operator.sign.replace("=", "")
                    query_operator = QueryOperator(normal_sign)
                    tmp = QueryExpression((expression.lhs, expression.rhs), (query_operator,))
                    stack = symbolize_expression(tmp)
                    return AssignmentExpressionInterpreter(tmp, reference, assignment_operator, stack)


