from typing import Union

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.Parser.Tokenizers.operator_tokenizers import QueryOperator
from mpl.interpreter.expression_evaluation.query_expression_interpreter import QueryExpressionInterpreter
from mpl.interpreter.expression_evaluation.assignmment_expression_interpreter import AssignmentExpressionInterpreter
from mpl.interpreter.expression_evaluation.operators import OperatorOperation, query_operations_dict, OperationType
from mpl.interpreter.expression_evaluation.query_expression_interpreter import symbolize_expression, \
    QueryExpressionInterpreter
from mpl.interpreter.expression_evaluation.scenario_expression_interpreter import ScenarioExpressionInterpreter
from mpl.interpreter.expression_evaluation.target_expression_interpreter import target_operations_dict, TargetExpressionInterpreter
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack, ExpressionInterpreter
from mpl.interpreter.expression_evaluation.assignmment_expression_interpreter import evaluate_assignment_expression, \
    AssignmentExpressionInterpreter
from mpl.interpreter.expression_evaluation.query_expression_interpreter import evaluate_symbolized_postfix_stack, symbolize_expression

assignment_operator = query_operations_dict['=']


def create_expression_interpreter(
        expression: Union[QueryExpression, AssignmentExpression, ScenarioExpression],
        as_target:bool = False
) -> ExpressionInterpreter:
    match expression:
        case QueryExpression() if as_target:
            stack = symbolize_expression(expression, target_operations_dict)
            return TargetExpressionInterpreter(expression, stack)
        case QueryExpression():
            stack = symbolize_expression(expression)
            return QueryExpressionInterpreter(expression, stack)
        case ScenarioExpression() as x:
            stack = symbolize_expression(expression.value)
            return ScenarioExpressionInterpreter(expression, stack)
        case AssignmentExpression():
            operator = query_operations_dict[expression.operator.contents]
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


