from abc import abstractmethod, ABC
from typing import Tuple, TypeVar, FrozenSet, Generic

T = TypeVar("T")


class Expression(ABC, Generic[T]):

    @abstractmethod
    def qualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> T:
        pass

    @abstractmethod
    def unqualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> T:
        pass

    @property
    @abstractmethod
    def reference_expressions(self) -> FrozenSet['ReferenceExpression']:
        pass

    @property
    def references(self) -> FrozenSet['Reference']:
        return frozenset({x.reference for x in self.reference_expressions})
