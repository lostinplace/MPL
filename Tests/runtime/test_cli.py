from itertools import zip_longest
from typing import Any

from parsita import Success
from prompt_toolkit import HTML

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine
from mpl.lib import fs
from mpl.runtime.cli.command_parser import SystemCommand, QueryCommand, ExploreCommand, ActivateCommand, TickCommand, \
    CommandParsers, LoadCommand
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
        '+test=`me`': ActivateCommand(quick_parse(AssignmentExpression, f"test=`me`")),
        '+a': ActivateCommand(quick_parse(AssignmentExpression, f"a={Ref('a').id}")),
        '.': TickCommand(1),
        '.1': TickCommand(1),
        '.2': TickCommand(2),
        '.301': TickCommand(301),
    }

    for text, expected_value in expectations.items():
        actual = CommandParsers.command.parse(text)
        expected = Success(expected_value)
        assert actual == expected


def test_command_execution():
    expressions = [
        quick_parse(RuleExpression, 'test -> no test')
    ]

    expectations = {
        'A->B->C': quick_parse(RuleExpression, 'A->B->C'),
        '+test =  5': {'test': (fs(), fs(5))},
        '+test': {'test': (fs(), fs(Ref('test').id))},
    }

    for command, expected_structure in expectations.items():
        engine = MPLEngine()
        engine.add(expressions)
        result = execute_command(engine, command)
        actual = result
        expected = expected_structure
        assert actual == expected


def test_command_sequences():
    expressions = [
        quick_parse(RuleExpression, 'test -> no test')
    ]

    expectations = {
        ('load Tests/test_files/simplest.mpl'): [
            None
        ],
        ('state one->state two', '+state one', '.', '.-1'): [
            None,
            {'state one': (fs(), fs(Ref('state one').id))},
            {
                'state one': (fs(Ref('state one').id), fs()),
                'state two': (fs(), fs(Ref('state one').id)),
            },
            {
                'state one': (fs(), fs(Ref('state one').id)),
                'state two': (fs(Ref('state one').id), fs()),
            },
        ],
        ('A->B->C', '.', '?A', '+A'): [
            quick_parse(RuleExpression, 'A->B->C'),
            None,
            {Ref('A'): fs()},
            None,
        ],
    }

    for commands, expected_structure in expectations.items():
        engine = MPLEngine()
        engine.add(expressions)
        for command, expected in zip_longest(commands, expected_structure):
            result = execute_command(engine, command)
            assert expected is None or result == expected