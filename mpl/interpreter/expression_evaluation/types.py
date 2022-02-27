from abc import ABC, abstractmethod
from numbers import Number
from typing import List, Union

from sympy import Expr

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.operators import OperatorOperation
from mpl.lib.query_logic import MPL_Context, FinalResultSet

postfix_stack = List[Union[Number, Reference, OperatorOperation]]
symbolized_postfix_stack = List[Union[Expr, OperatorOperation]]


class ExpressionResult(ABC):

    value: FinalResultSet


QueryLedgerRef = Reference('{}')
ChangeLedgerRef = Reference('{CHANGES}')

class ExpressionInterpreter(ABC):

    @abstractmethod
    def interpret(self, context: MPL_Context) -> ExpressionResult:
        pass