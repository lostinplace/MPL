from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Set, FrozenSet

from parsita import TextParsers, opt, Success, reg, longest, repsep, lit

from mpl.Parser.ExpressionParsers.assignment_expression_parser \
    import AssignmentExpression, AssignmentExpressionParsers as AExpP
from mpl.Parser.ExpressionParsers.machine_expression_parser import parse_machine_file
from mpl.Parser.ExpressionParsers.reference_expression_parser \
    import ReferenceExpression, ReferenceExpressionParsers as RefExP, Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleExpressionParsers
from mpl.lib import fs

"""
Command	Effect
{rule}	Add Rule to current engine
.	increments the state of the engine, then prints the active references
.{n}	increments the state of the engine n times then prints the active references
+{name}	activates the named reference
+{name} = {value}	activates the named reference with the provided value
explore {n}	conducts an exploration of n iterations and prints the distribution of outcomes
?	prints the current engine context
?{name}	prints the state of the named reference
quit	exits the environment
help	shows the list of commands
"""


class SystemCommand(Enum):
    QUIT = auto()
    HELP = auto()
    LIST = auto()


@dataclass(frozen=True, order=True)
class LoadCommand:
    path: str

    def load(self) -> FrozenSet[RuleExpression]:
        result = parse_machine_file(self.path)
        return frozenset(result)

    @staticmethod
    def interpret(path_components: List[List[str]]) -> 'LoadCommand':
        leading_slash = '/' if path_components[0] else ''
        remaining_path = leading_slash + '/'.join(path_components[1])
        return LoadCommand(remaining_path)


@dataclass(frozen=True, order=True)
class TickCommand:
    number: int = 1

    @staticmethod
    def interpret(text=[]):
        count = 1 if not text else text[0]
        return TickCommand(int(count))


@dataclass(frozen=True, order=True)
class ExploreCommand:
    number: int = 1

    @staticmethod
    def interpret(text=[]):
        count = 1 if not text else text[0]
        return ExploreCommand(int(count))


@dataclass(frozen=True, order=True)
class QueryCommand:
    reference: Reference = None

    @staticmethod
    def interpret(text=[]):
        match text:
            case []:
                return QueryCommand(None)
            case [ReferenceExpression()] as ref:
                return QueryCommand(ref[0].value)


@dataclass(frozen=True, order=True)
class ActivateCommand:
    expression: AssignmentExpression

    @staticmethod
    def interpret(expression: ReferenceExpression | AssignmentExpression):
        match expression:
            case ReferenceExpression():
                reference = expression.value
                value = reference.id
                expr_input = f'{reference.name}={value}'
                expr = AExpP.expression.parse(expr_input)
                assert isinstance(expr, Success)

                return ActivateCommand(expr.value)
            case AssignmentExpression():
                return ActivateCommand(expression)

        return ActivateCommand(expression)


class CommandParsers(TextParsers):
    filepath = opt('/') & repsep(reg(r'[^/]+'), '/', min=1)
    load = lit('load') >> filepath > LoadCommand.interpret

    tick = reg(r'\.') >> opt(reg(r'\d+')) > TickCommand.interpret
    assign = '+' >> longest(RefExP.expression, AExpP.expression) > ActivateCommand.interpret
    explore = 'explore' >> opt(reg(r'\d+')) > ExploreCommand.interpret
    query = '?' >> opt(RefExP.expression) > QueryCommand.interpret
    quit = reg('quit') > (lambda _: SystemCommand.QUIT)
    help = reg('help') > (lambda _: SystemCommand.HELP)
    list = reg('list') > (lambda _: SystemCommand.LIST)
    system = quit | help | list

    command = longest(system, tick, assign, explore, query, load, RuleExpressionParsers.expression)


