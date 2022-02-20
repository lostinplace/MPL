from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Any

from mpl.lib.query_logic import query_negate, query_xor, query_and, query_or


class OperationType(Enum):
    NumericAlgebra = auto()
    Logical = auto()
    Unary = auto()
    Assign = auto()
    Increment = auto()


@dataclass(frozen=True, order=True)
class OperatorOperation:
    sign: str
    score: int
    operation_type: OperationType
    method: Callable[[Any, Any], Any]


operations = [
    OperatorOperation('!', 9, OperationType.Unary, query_negate),
    OperatorOperation('**', 8, OperationType.NumericAlgebra, lambda x, y: x ** y),
    OperatorOperation('*', 7, OperationType.NumericAlgebra, lambda x, y: x * y),
    OperatorOperation('/', 7, OperationType.NumericAlgebra, lambda x, y: x / y),
    OperatorOperation('+', 6, OperationType.NumericAlgebra, lambda x, y: x + y),
    OperatorOperation('-', 6, OperationType.NumericAlgebra, lambda x, y: x - y),
    OperatorOperation('==', 5, OperationType.Logical, lambda x, y: x == y),
    OperatorOperation('!=', 5, OperationType.Logical, lambda x, y: x != y),
    OperatorOperation('>', 5, OperationType.Logical, lambda x, y: x > y),
    OperatorOperation('>=', 5, OperationType.Logical, lambda x, y: x >= y),
    OperatorOperation('<', 5, OperationType.Logical, lambda x, y: x < y),
    OperatorOperation('<=', 5, OperationType.Logical, lambda x, y: x <= y),
    OperatorOperation('^', 4, OperationType.Logical, query_xor),
    OperatorOperation('&', 3, OperationType.Logical, query_and),
    OperatorOperation('|', 2, OperationType.Logical, query_or),
    OperatorOperation('+=', 1, OperationType.Increment, lambda x, y: x + y),
    OperatorOperation('-=', 1, OperationType.Increment, lambda x, y: x - y),
    OperatorOperation('*=', 1, OperationType.Increment, lambda x, y: x * y),
    OperatorOperation('/=', 1, OperationType.Increment, lambda x, y: x / y),
    OperatorOperation('&=', 1, OperationType.Increment, lambda x, y: query_and),
    OperatorOperation('|=', 1, OperationType.Increment, lambda x, y: query_or),
    OperatorOperation('^=', 1, OperationType.Increment, lambda x, y: query_xor),
    OperatorOperation('=',  0, OperationType.Assign   , lambda x, y: x),
]

query_operations_dict = dict([(x.sign, x) for x in operations])
