from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Any

from mpl.lib.logic import logic_negate, logic_xor, logic_and, logic_or


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
    OperatorOperation('!', 9, OperationType.Unary, logic_negate), #done
    OperatorOperation('**', 8, OperationType.NumericAlgebra, lambda x, y: x ** y), #done
    OperatorOperation('*', 7, OperationType.NumericAlgebra, lambda x, y: x * y), #done
    OperatorOperation('/', 7, OperationType.NumericAlgebra, lambda x, y: x / y), #done
    OperatorOperation('+', 6, OperationType.NumericAlgebra, lambda x, y: x + y), #done
    OperatorOperation('-', 6, OperationType.NumericAlgebra, lambda x, y: x - y), #done
    OperatorOperation('==', 5, OperationType.Logical, lambda x, y: x == y),
    OperatorOperation('!=', 5, OperationType.Logical, lambda x, y: x != y),
    OperatorOperation('>', 5, OperationType.Logical, lambda x, y: x > y),
    OperatorOperation('>=', 5, OperationType.Logical, lambda x, y: x >= y),
    OperatorOperation('<', 5, OperationType.Logical, lambda x, y: x < y),
    OperatorOperation('<=', 5, OperationType.Logical, lambda x, y: x <= y),
    OperatorOperation('^', 4, OperationType.Logical, logic_xor), #done
    OperatorOperation('&', 3, OperationType.Logical, logic_and), #done
    OperatorOperation('|', 2, OperationType.Logical, logic_or), #done

    OperatorOperation('=',  0, OperationType.Assign   , lambda x, y: x),  # done
    OperatorOperation('+=', 1, OperationType.Increment, lambda x, y: x + y),  # done
    OperatorOperation('-=', 1, OperationType.Increment, lambda x, y: x - y),  # done
    OperatorOperation('*=', 1, OperationType.Increment, lambda x, y: x * y),  # done
    OperatorOperation('/=', 1, OperationType.Increment, lambda x, y: x / y),  # done
    OperatorOperation('&=', 1, OperationType.Increment, lambda x, y: logic_and),  # done
    OperatorOperation('|=', 1, OperationType.Increment, lambda x, y: logic_or),  # done
    OperatorOperation('^=', 1, OperationType.Increment, lambda x, y: logic_xor),  # done
]
op_dict = dict([(x.sign, x) for x in operations])