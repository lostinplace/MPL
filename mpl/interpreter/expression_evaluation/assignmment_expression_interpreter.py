import dataclasses
import itertools

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.query_expression_interpreter import symbolized_postfix_stack, \
    evaluate_symbolized_postfix_stack
from mpl.interpreter.expression_evaluation import OperatorOperation
from mpl.interpreter.expression_evaluation.operators import OperationType
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity
from mpl.lib.logic import MPL_Context


def evaluate_assignment_expression(
        reference: Reference,
        operation: OperatorOperation,
        symbolized_stack: symbolized_postfix_stack,
        context:MPL_Context
) -> MPL_Context:
    """
    Evaluate the assignment expression.
    :param expression: AssignmentExpression
    :param symbolized_stack: symbolized_postfix_stack
    :return: None
    """

    increment_value = evaluate_symbolized_postfix_stack(symbolized_stack, context)
    existing_value = context[reference]
    match existing_value:
        case MPLEntity():
            new_value = dataclasses.replace(existing_value, value=increment_value)
        case _:
            new_value = increment_value

    return {reference: new_value}
