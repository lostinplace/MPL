from dataclasses import dataclass
from typing import Type, Optional, Union
from Parser.expression_parser import Label, Assignment, Expression
from enum import Enum


class TransitionType(Enum):
    HARD = 0
    SOFT = 1
    LOCKING = 2


@dataclass(frozen=True, order=True)
class Declaration:
    item: object


@dataclass(frozen=True, order=True)
class Event:
    name: Label


@dataclass(frozen=True, order=True)
class State:
    label: Label
    parent: Optional[Type["State"]]
    exclusive: bool


@dataclass(frozen=True, order=True)
class Machine:
    id: str


@dataclass(frozen=True, order=True)
class Trigger:
    Event: Union[Label, Expression]
    goal: State
    type: TransitionType


@dataclass(frozen=True, order=True)
class Invocation:
    call: str


@dataclass(frozen=True, order=True)
class Action:
    effect: Union[Assignment, Event, Invocation]
    type: TransitionType


@dataclass(frozen=True, order=True)
class Transition:
    origin: Label
    goal: Label
    type: TransitionType
    triggers: list[Union[Event, Label, State, Expression, Invocation]]
    actions: list[Action]


@dataclass(frozen=True, order=True)
class Condition:
    expression: Union[Expression, Label, Event]


@dataclass(frozen=True, order=True)
class Rule:
    operations: list[Union[Action, Condition]]


@dataclass(frozen=True, order=True)
class Trigger:
    target: State


default_state = lambda name: State(Label(name), None, False)