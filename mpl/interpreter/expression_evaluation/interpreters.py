import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass
from numbers import Number
from typing import Tuple, FrozenSet, Union, Optional, Dict

from sympy import Expr

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.Parser.Tokenizers.operator_tokenizers import QueryOperator
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.operators import OperatorOperation, query_operations_dict, OperationType
from mpl.interpreter.expression_evaluation.stack_management import evaluate_symbolized_postfix_stack, \
    symbolize_expression
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack, ExpressionResult
from mpl.lib.context_tree.context_tree_implementation import ContextTree
from mpl.lib.query_logic import target_xor, target_and, target_or


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


@dataclasses.dataclass(frozen=True, order=True)
class AssignmentResult:
    value: EntityValue
    change: Dict[Reference, EntityValue]


class ExpressionInterpreter(ABC):

    @abstractmethod
    def interpret(self, context: ContextTree) -> ExpressionResult:
        pass

    @property
    @abstractmethod
    def references(self) -> FrozenSet[Reference]:
        pass

    @staticmethod
    def from_expression(
        expression:  QueryExpression | ScenarioExpression | AssignmentExpression,
        target: bool = False
    ) -> 'ExpressionInterpreter':
        return create_expression_interpreter(expression, target)


@dataclasses.dataclass(frozen=True, order=True)
class AssignmentExpressionInterpreter(ExpressionInterpreter):
    expression: AssignmentExpression
    reference: Reference
    symbolized: symbolized_postfix_stack

    def interpret(self, context: ContextTree) -> AssignmentResult:
        from mpl.lib.context_tree.context_tree_implementation import change_node
        target_value = evaluate_symbolized_postfix_stack(self.symbolized, context)
        change = change_node(context.root, self.reference, target_value)
        return AssignmentResult(target_value, change)

    @property
    def references(self) -> FrozenSet[Reference]:
        result = {self.reference} | self.expression.references
        return frozenset(result)


def create_expression_interpreter(
        expression: Union[QueryExpression, AssignmentExpression, ScenarioExpression],
        as_target: bool = False
) -> ExpressionInterpreter:
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


@dataclasses.dataclass(frozen=True, order=True)
class QueryResult(ExpressionResult):
    value: EntityValue


@dataclass(frozen=True, order=True)
class QueryExpressionInterpreter(ExpressionInterpreter):

    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: ContextTree) -> QueryResult:
        result = evaluate_symbolized_postfix_stack(self.symbolized, context)
        return QueryResult(result)

    @staticmethod
    def get_references_from_qri_like(qri: Union['QueryExpressionInterpreter', 'TargetExpressionInterpreter']) \
            -> FrozenSet[Reference]:
        result = set()
        for symbol in qri.symbolized:
            match symbol:
                case Expr():
                    symbols = symbol.free_symbols
                    decoded = {Reference.decode(symbol) for symbol in symbols}
                    result |= decoded

        return frozenset(result)

    @property
    def references(self) -> FrozenSet[Reference]:
        return QueryExpressionInterpreter.get_references_from_qri_like(self)


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


@dataclasses.dataclass(frozen=True, order=True)
class TargetResult(ExpressionResult):
    value: EntityValue


target_operations = {
    '^': OperatorOperation('^', 4, OperationType.Logical, target_xor),
    '&': OperatorOperation('&', 3, OperationType.Logical, target_and),
    '|': OperatorOperation('|', 2, OperationType.Logical, target_or),
}

target_operations_dict = query_operations_dict | target_operations


@dataclass(frozen=True, order=True)
class TargetExpressionInterpreter(ExpressionInterpreter):

    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: ContextTree) -> TargetResult:
        result = evaluate_symbolized_postfix_stack(self.symbolized, context, True)
        return TargetResult(result)

    @property
    def references(self) -> FrozenSet[Reference]:
        return QueryExpressionInterpreter.get_references_from_qri_like(self)
