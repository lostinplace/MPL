from __future__ import annotations

import dataclasses
import enum
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from numbers import Number
from typing import Tuple, List, Any, FrozenSet, Union, Optional
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from sympy import Expr


@dataclass(frozen=True, order=True)
class MPLEntity:
    name: str
    value: Optional[FrozenSet[Expr | Number | str]] = frozenset()

    def __add__(self, other):
        pass

    @staticmethod
    def from_reference(reference: Reference, value: FrozenSet[Expr | Number | str] = frozenset()):
        return MPLEntity(reference.name, value)







