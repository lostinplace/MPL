from __future__ import annotations


from abc import ABC, abstractmethod
from typing import FrozenSet


from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.expression_evaluation.types import ExpressionResult


class ExpressionInterpreter(ABC):

    @abstractmethod
    def interpret(self, context: EngineContext) -> ExpressionResult:
        pass

    @property
    @abstractmethod
    def references(self) -> FrozenSet[Reference]:
        pass

    @staticmethod
    def from_expression(
        expression:  'QueryExpression' | 'ScenarioExpression' | 'AssignmentExpression',
        target: bool = False
    ) -> 'ExpressionInterpreter':
        from mpl.interpreter.expression_evaluation.interpreters.create_expression_interpreter import \
            create_expression_interpreter
        return create_expression_interpreter(expression, target)