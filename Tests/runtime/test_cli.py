from itertools import zip_longest
from typing import Any

from parsita import Success
from prompt_toolkit import HTML

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref, SRef
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.expression_evaluation.entity_value import ev_fv
from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine
from mpl.lib import fs
from mpl.runtime.cli.command_parser import SystemCommand, QueryCommand, ExploreCommand, ActivateCommand, TickCommand, \
    CommandParsers, LoadCommand, MemoryType, SaveCommand
from mpl.runtime.cli.mplsh import execute_command


def test_command_parsing():
    expectations = {
        'list': SystemCommand.LIST,
        'load Tests/test_files/simplest.mpl': LoadCommand('Tests/test_files/simplest.mpl'),
        'A -> B -> C': quick_parse(RuleExpression, 'A -> B -> C'),
        'help': SystemCommand.HELP,
        'quit': SystemCommand.QUIT,
        '?test': QueryCommand(Ref('test')),
        '?': QueryCommand(),
        'explore 13': ExploreCommand(13),
        'explore': ExploreCommand(1),
        '+a': ActivateCommand(quick_parse(AssignmentExpression, f"a=True")),
        '.': TickCommand(1),
        '.1': TickCommand(1),
        '.2': TickCommand(2),
        '.301': TickCommand(301),
    }

    for text, expected_value in expectations.items():
        actual = CommandParsers.command.parse(text)
        expected = Success(expected_value)
        assert actual == expected, text


def test_command_execution():
    expressions = [
        quick_parse(RuleExpression, 'test -> no test')
    ]

    expectations = {
        '+test': {
            Ref('test'): (ev_fv(), ev_fv(True)),
            Ref('test.*'): (ev_fv(True), ev_fv()),
        },
        'add A->B->C': f'Incorporated Rule: {quick_parse(RuleExpression, "A->B->C")}',
    }

    for command, expected_structure in expectations.items():
        engine = MPLEngine()
        engine.add(expressions)
        result = execute_command(engine, command)
        actual = result
        expected = expected_structure
        assert actual == expected, command


def test_command_sequences():
    expressions = {
        quick_parse(RuleExpression, 'test -> no test')
    }

    expectations = [
        {
            'load Tests/test_files/simplest.mpl': None,
            '+Three': {
                SRef('Three'): (ev_fv(3), ev_fv(True)),
            },
            'clear context': None,
            '?': {}
        },
        {
            'add state one->state two': f'Incorporated Rule: {quick_parse(RuleExpression, "state one->state two")}',
            '+state one': {
                Ref('state one'): (ev_fv(), ev_fv(True)),
                Ref('state one.*'): (ev_fv(True), ev_fv()),
            },
            '.': {
                Ref('state one'): (ev_fv(True), ev_fv()),
                Ref('state one.*'): (ev_fv(), ev_fv(True)),
                Ref('state two'): (ev_fv(), ev_fv(Ref('state one'), True)),
                Ref('state two.*'): (ev_fv(True), ev_fv())
            },
            '.-1': {
                Ref('state one'): (ev_fv(), ev_fv(True)),
                Ref('state one.*'): (ev_fv(True), ev_fv()),
                Ref('state two'): (ev_fv(Ref('state one'), True), ev_fv()),
                Ref('state two.*'): (ev_fv(), ev_fv(True))
            },
        },
        {
            'load Tests/test_files/simplest.mpl': None
        },
        {
            'add A->B->C': f'Incorporated Rule: {quick_parse(RuleExpression, "A->B->C")}',
            '.': None,
            '?A': {
                Ref('A'): ev_fv(),
            },
            '+A': None,
        },
    ]

    for command_sequence in expectations:
        engine = MPLEngine()
        engine.add(expressions)
        for command, expected in command_sequence.items():
            result = execute_command(engine, command)
            if expected is not None:
                assert result == expected, command


def test_basic_command_parsing():
    expectations = {
        'load /foo/bar': LoadCommand('/foo/bar'),
        'load context from /foo/bar': LoadCommand('/foo/bar', MemoryType.CONTEXT),
        'load rules from foo/bar': LoadCommand('foo/bar', MemoryType.RULES),
        'save scratch.mpl': SaveCommand('scratch.mpl', MemoryType.ALL),
    }

    for input, expected in expectations.items():
        assert CommandParsers.command.parse(input) == Success(expected)


def test_flashlight():
    engine = MPLEngine()
    execute_command(engine, 'load Tests/test_files/flashlight.mpl')
    execute_command(engine, '.')
    tmp = execute_command(engine, '?flashlight.battery.charge.empty')
    assert tmp == {
        Ref('flashlight.battery.charge.empty'): ev_fv(),
    }
    execute_command(engine, '+flashlight.battery.inserted')
    execute_command(engine, '.')
    execute_command(engine, '.')
    tmp = execute_command(engine, '?flashlight.battery.charge.empty')
    assert tmp == {
        Ref('flashlight.battery.charge.empty'): ev_fv(True),
    }
    execute_command(engine, 'flashlight.battery.level = 0.5')
    execute_command(engine, '.')
    tmp = execute_command(engine, '?flashlight.battery.charge.low')
    assert tmp == {
        Ref('flashlight.battery.charge.low'): ev_fv(True),
    }
    tmp = execute_command(engine, '?flashlight.battery.charge.empty')
    assert tmp == {
        Ref('flashlight.battery.charge.empty'): ev_fv(),
    }
    tmp = execute_command(engine, 'flashlight.battery.level = 0')
    execute_command(engine, '.')
    tmp = execute_command(engine, '?flashlight.battery.charge.empty')
    assert tmp == {
        Ref('flashlight.battery.charge.empty'): ev_fv(True),
    }
    tmp = execute_command(engine, '?flashlight.battery.charge.low')
    assert tmp == {
        Ref('flashlight.battery.charge.low'): ev_fv(),
    }
    execute_command(engine, 'flashlight.battery.level = 0.5')
    execute_command(engine, '+flashlight.power.on')
    execute_command(engine, '.')
    execute_command(engine, '.')
    tmp = execute_command(engine, '?Beam')
    assert tmp == {
        Ref('Beam'): ev_fv(True),
    }
    execute_command(engine, '+flashlight.broken')
    execute_command(engine, '.')
    tmp = execute_command(engine, '?Beam')
    assert tmp == {
        Ref('Beam'): ev_fv(),
    }



