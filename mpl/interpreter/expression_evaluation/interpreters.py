import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass
from numbers import Number
from typing import Tuple, FrozenSet, Union, Optional

from sympy import Expr

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.Parser.Tokenizers.operator_tokenizers import QueryOperator
from mpl.interpreter.expression_evaluation.operators import OperatorOperation, query_operations_dict, OperationType
from mpl.interpreter.expression_evaluation.stack_management import evaluate_symbolized_postfix_stack, \
    symbolize_expression
from mpl.interpreter.expression_evaluation.types import symbolized_postfix_stack, ChangeLedgerRef, ExpressionResult
from mpl.interpreter.reference_resolution.mpl_entity import MPLEntity
from mpl.lib.query_logic import MPL_Context, FinalResultSet, target_xor, target_and, target_or


def evaluate_assignment_expression(
        reference: Reference,
        symbolized_stack: symbolized_postfix_stack,
        context: MPL_Context
) -> Tuple[Reference, FinalResultSet]:

    increment_value = evaluate_symbolized_postfix_stack(symbolized_stack, context)
    existing_value = context[reference]
    match existing_value:
        case MPLEntity():
            new_value = dataclasses.replace(existing_value, value=increment_value)
        case _:
            new_value = increment_value

    return reference, new_value


@dataclass(frozen=True, order=True)
class AssignmentResult:
    value: MPL_Context


class ExpressionInterpreter(ABC):

    @abstractmethod
    def interpret(self, context: MPL_Context) -> ExpressionResult:
        pass

    def generate_context(self) -> MPL_Context:
        return MPL_Context(self.get_references())

    @property
    @abstractmethod
    def references(self) -> FrozenSet[Reference]:
        pass

    @staticmethod
    def from_expression(
        expression:  QueryExpression|ScenarioExpression|AssignmentExpression,
        target: bool = False
    ) -> 'ExpressionInterpreter':
        return create_expression_interpreter(expression, target)


@dataclass(frozen=True, order=True)
class AssignmentExpressionInterpreter(ExpressionInterpreter):
    def generate_context(self) -> MPL_Context:
        pass

    expression: AssignmentExpression
    reference: Reference
    symbolized: symbolized_postfix_stack

    def interpret(self, context: MPL_Context) -> AssignmentResult:
        change = evaluate_assignment_expression(self.reference, self.symbolized, context)
        existing_changes = context.get(ChangeLedgerRef) or dict()
        change = {change[0]: change[1]}
        update = {ChangeLedgerRef: existing_changes | change}
        result = context | change | update
        return AssignmentResult(value=result)

    @property
    def references(self) -> FrozenSet[Reference]:
        result = {self.reference}
        for symbol in self.symbolized:
            match symbol:
                case Expr():
                    symbols = symbol.free_symbols
                    result |= {Reference.decode(symbol) for symbol in symbols}

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
                    return AssignmentExpressionInterpreter(tmp, reference, stack)


@dataclass(frozen=True, order=True)
class QueryResult(ExpressionResult):
    value: FinalResultSet


@dataclass(frozen=True, order=True)
class QueryExpressionInterpreter(ExpressionInterpreter):

    expression: QueryExpression
    symbolized: symbolized_postfix_stack

    def interpret(self, context: MPL_Context) -> QueryResult:
        result = evaluate_symbolized_postfix_stack(self.symbolized, context)
        return QueryResult(result)

    @staticmethod
    def get_references_from_qri_like(qri: 'QueryExpressionInterpreter') -> FrozenSet[Reference]:
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

    @property
    def references(self) -> FrozenSet[Reference]:
        return QueryExpressionInterpreter.get_references_from_qri_like(self)


@dataclass(frozen=True, order=True)
class TargetResult(ExpressionResult):
    value: FinalResultSet


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

    def interpret(self, context: MPL_Context) -> TargetResult:
        result = evaluate_symbolized_postfix_stack(self.symbolized, context, True)
        return TargetResult(result)

    @property
    def references(self) -> FrozenSet[Reference]:
        return QueryExpressionInterpreter.get_references_from_qri_like(self)
