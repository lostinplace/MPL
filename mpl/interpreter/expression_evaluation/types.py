from abc import ABC
from numbers import Number
from typing import List, Union, Tuple

from sympy import Expr

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.operators import OperatorOperation


postfix_stack = List[Union[Number, Reference, OperatorOperation]]
symbolized_postfix_stack = Tuple[Union[Expr, OperatorOperation],...]


class ExpressionResult(ABC):

    value: EntityValue


QueryLedgerRef = Reference('{}')
ChangeLedgerRef = Reference('{CHANGES}')


