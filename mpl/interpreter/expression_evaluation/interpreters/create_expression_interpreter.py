from __future__ import annotations

from typing import Union

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.Tokenizers.operator_tokenizers import QueryOperator
from mpl.interpreter.expression_evaluation.interpreters.assignment_expression_interpreter import \
    AssignmentExpressionInterpreter
from mpl.interpreter.expression_evaluation.interpreters.expression_interpreter import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.interpreters.query_expression_interpreter import QueryExpressionInterpreter
from mpl.interpreter.expression_evaluation.interpreters.scenario_expression_interpreter import \
    ScenarioExpressionInterpreter
from mpl.interpreter.expression_evaluation.interpreters.target_exprression_interpreter import target_operations_dict, \
    TargetExpressionInterpreter
from mpl.interpreter.expression_evaluation.operators import query_operations_dict, OperationType
from mpl.interpreter.expression_evaluation.stack_management import symbolize_expression


def create_expression_interpreter(
        expression: Union[QueryExpression, AssignmentExpression, 'ScenarioExpression'],
        as_target: bool = False
) -> ExpressionInterpreter:
    from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
    match expression:
        case QueryExpression() if as_target:
            stack = symbolize_expression(expression, target_operations_dict)
            return TargetExpressionInterpreter(expression, stack)
        case QueryExpression():
            stack = symbolize_expression(expression)
            return QueryExpressionInterpreter(expression, stack)
        case ScenarioExpression():
            stack = symbolize_expression(expression.value)
            return ScenarioExpressionInterpreter(expression, stack)
        case AssignmentExpression():
            operator = query_operations_dict[expression.operator.contents]
            reference = expression.lhs.reference
            match operator.operation_type:
                case OperationType.Assign:
                    stack = symbolize_expression(expression.rhs)
                    return AssignmentExpressionInterpreter(expression, reference, stack)
                case OperationType.Increment:
                    normal_sign = operator.sign.replace("=", "")
                    query_operator = QueryOperator(normal_sign)
                    tmp = QueryExpression((expression.lhs, expression.rhs), (query_operator,))
                    stack = symbolize_expression(tmp)
                    return AssignmentExpressionInterpreter(expression, reference, stack)