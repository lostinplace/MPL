import os

from parsita import Success
from prompt_toolkit import print_formatted_text as print, HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.validation import Validator
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleClause
from mpl.interpreter.conflict_resolution import identify_conflicts, resolve_conflicts
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.rule_evaluation import RuleInterpreter
from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine
from mpl.runtime.cli.command_parser import CommandParsers, SystemCommand, TickCommand, ExploreCommand, QueryCommand, \
    ActivateCommand, LoadCommand

completer = NestedCompleter.from_nested_dict({
    'help': None,
    'quit': None,
    'explore': None,
})


def is_valid_command(text):
    result = CommandParsers.command.parse(text)
    return isinstance(result, Success)


validator = Validator.from_callable(
    is_valid_command,
    error_message='Invalid commmand',
    move_cursor_to_end=True)


class Toolbar:
    outer_track = 1

    @staticmethod
    def bottom_toolbar():
        Toolbar.outer_track += 1
        return [('class:bottom-toolbar', f'entries = {Toolbar.outer_track}')]


style = Style.from_dict({
    'bottom-toolbar': '#ffffff bg:#333333',
})

bindings = KeyBindings()


def execute_command(engine: MPLEngine, command: str):
    result = CommandParsers.command.parse(command)
    value = result.value
    match value:
        case SystemCommand.QUIT:
            return value
        case SystemCommand.HELP:
            return 'Help'
        case SystemCommand.LIST:
            expressions = {x.name for x in engine.rule_interpreters}
            return expressions
        case RuleExpression():
            engine.add(value)
            return value
        case LoadCommand():
            expressions = value.load()
            engine.add(expressions)
            result = {str(x) for x in expressions}
            return result
        case TickCommand():
            start_context = engine.context
            for _ in range(value.number):
                engine.tick()
            end_context = engine.context
            result = start_context.get_diff(end_context)
            return result
        case ExploreCommand() as explore_command:
            # TODO: explore command
            return explore_command
        case QueryCommand() as query_command:
            match query_command.reference:
                case Reference():
                    tmp = engine.query(query_command.reference)
                    return {query_command.reference: tmp}
                case None:
                    result = engine.context
                    return result
        case ActivateCommand() as activate_command:
            re = RuleExpression((RuleClause('assign', activate_command.expression),), tuple())
            interpreter = RuleInterpreter.from_expression(re)
            rule_context = EngineContext.from_interpreter(interpreter)
            engine.context = rule_context | engine.context
            result = interpreter.interpret(engine.context)
            conflicts = identify_conflicts([result])
            resolved = resolve_conflicts(conflicts)
            result = engine.apply(resolved)
            return result




def run_interactive_session():
    history_path = f'{os.path.expanduser("~")}/.mplsh_history'
    our_history = FileHistory(history_path)
    session = PromptSession(history=our_history)
    prompt_kwargs = {
        'completer': completer,
        'auto_suggest': AutoSuggestFromHistory(),
        'validator': validator,
        'style': style,
        'key_bindings': bindings,
        'bottom_toolbar': Toolbar.bottom_toolbar,
    }
    engine = MPLEngine()

    while True:
        command = session.prompt('>  ', **prompt_kwargs)
        command_result = execute_command(engine, command)
        if command_result == SystemCommand.QUIT:
            return

        print(command_result)


if __name__ == '__main__':
    run_interactive_session()
