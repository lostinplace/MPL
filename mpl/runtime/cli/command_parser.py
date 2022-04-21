from dataclasses import dataclass
from enum import Enum, auto, IntFlag
from typing import List, Set, FrozenSet, Optional

from parsita import TextParsers, opt, Success, reg, longest, repsep, lit
from parsita.util import splat

from mpl.Parser.ExpressionParsers.assignment_expression_parser \
    import AssignmentExpression, AssignmentExpressionParsers as AExpP
from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile
from mpl.Parser.ExpressionParsers.reference_expression_parser \
    import ReferenceExpression, ReferenceExpressionParsers as RefExP, Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleExpressionParsers
from mpl.interpreter.reference_resolution.mpl_ontology import engine_to_string
from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine
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


class MemoryType(IntFlag):
    CONTEXT = auto()
    RULES = auto()
    ALL = CONTEXT | RULES


@dataclass(frozen=True, order=True)
class LoadCommand:
    path: str
    type: MemoryType = MemoryType.ALL

    def load(self) -> MPLEngine:
        return MPLEngine.from_file(self.path)

    @staticmethod
    def interpret(type: List[str], path_components: List[List[str]]) -> 'LoadCommand':
        leading_slash = '/' if path_components[0] else ''
        remaining_path = leading_slash + '/'.join(path_components[1])
        mt: MemoryType = MemoryType.ALL
        match type:
            case ['rules']:
                mt = MemoryType.RULES
            case ['context']:
                mt = MemoryType.CONTEXT

        return LoadCommand(remaining_path, mt)


@dataclass(frozen=True, order=True)
class SaveCommand:
    path: str
    type: MemoryType = MemoryType.ALL

    def save(self, engine: MPLEngine) -> None:
        match self.type:
            case MemoryType.CONTEXT:
                content = str(engine.context)
            case MemoryType.RULES:
                content = str(engine)
            case _:
                content = engine_to_string(engine)

        with open(self.path, 'w') as f:
            f.write(content)

    @staticmethod
    def interpret(type: List[str], path_components: List[List[str]]) -> 'LoadCommand':
        leading_slash = '/' if path_components[0] else ''
        remaining_path = leading_slash + '/'.join(path_components[1])
        mt: MemoryType = MemoryType.ALL
        match type:
            case ['rules']:
                mt = MemoryType.RULES
            case ['context']:
                mt = MemoryType.CONTEXT

        return SaveCommand(remaining_path, mt)


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
    reference: Optional[Reference] = None

    @staticmethod
    def interpret(text=[]):
        match text:
            case []:
                return QueryCommand(None)
            case [ReferenceExpression() as x]:
                return QueryCommand(x.reference)


@dataclass(frozen=True, order=True)
class AddRuleCommand:
    expression: RuleExpression


@dataclass(frozen=True, order=True)
class DropRuleCommand:
    expression: RuleExpression




@dataclass(frozen=True, order=True)
class ClearCommand:
    memory_type: MemoryType = MemoryType.ALL

    @staticmethod
    def interpret(text=[]):
        match text:
            case ['context']:
                return ClearCommand(MemoryType.CONTEXT)
            case ['rules']:
                return ClearCommand(MemoryType.RULES)
            case ['all']:
                return ClearCommand(MemoryType.ALL)
        return ClearCommand(MemoryType.ALL)


@dataclass(frozen=True, order=True)
class ActivateCommand:
    expression: AssignmentExpression

    @staticmethod
    def interpret(expression: ReferenceExpression | AssignmentExpression):
        match expression:
            case ReferenceExpression():
                reference = expression.reference
                value = reference.id
                expr_input = f'{reference.name}={True}'
                expr = AExpP.expression.parse(expr_input)
                assert isinstance(expr, Success)

                return ActivateCommand(expr.value)
            case AssignmentExpression():
                return ActivateCommand(expression)

        return ActivateCommand(expression)

    @staticmethod
    def deactivate(expression: ReferenceExpression):
        reference = expression.reference
        expr_input = f'{reference.name}=0'
        expr = AExpP.expression.parse(expr_input)
        assert isinstance(expr, Success)
        return ActivateCommand(expr.value)


class CommandParsers(TextParsers):
    filepath = opt('/') & repsep(reg(r'[^/]+'), '/', min=1)
    load = lit('load') >> opt((lit('rules') | 'context') << 'from') & filepath > splat(LoadCommand.interpret)
    save = lit('save') >> opt((lit('rules') | 'context') << 'to') & filepath > splat(SaveCommand.interpret)

    tick = reg(r'\.') >> opt(reg(r'-?\d+')) > TickCommand.interpret
    activate = '+' >> RefExP.expression > ActivateCommand.interpret
    deactivate = '-' >> RefExP.expression > ActivateCommand.deactivate

    explore = 'explore' >> opt(reg(r'\d+')) > ExploreCommand.interpret
    query = '?' >> opt(RefExP.expression) > QueryCommand.interpret
    add_rule = 'add' >> RuleExpressionParsers.expression > AddRuleCommand
    drop_rule = 'drop' >> RuleExpressionParsers.expression > DropRuleCommand

    clear = 'clear' >> opt(lit('all') | 'context' | 'rules') > ClearCommand.interpret
    quit = reg('quit') > (lambda _: SystemCommand.QUIT)
    help = reg('help') > (lambda _: SystemCommand.HELP)
    list = reg('list') > (lambda _: SystemCommand.LIST)

    system = quit | help | list | clear

    command = longest(system, tick, activate, deactivate, explore, add_rule, query, load, save, RuleExpressionParsers.expression)


def test_command_parsing():
    expectations = {
        'load /foo/bar': LoadCommand('/foo/bar'),
        'load context from /foo/bar': LoadCommand('/foo/bar', MemoryType.CONTEXT),
        'load rules from foo/bar': LoadCommand('foo/bar', MemoryType.RULES),
        'save scratch.mpl': SaveCommand('scratch.mpl', MemoryType.ALL),
    }

    for input, expected in expectations.items():
        assert CommandParsers.command.parse(input) == Success(expected)