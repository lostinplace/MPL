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
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity
from mpl.interpreter.rule_evaluation import RuleInterpreter
from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine
from mpl.runtime.cli.command_parser import CommandParsers, SystemCommand, TickCommand, ExploreCommand, QueryCommand, \
    ActivateCommand, LoadCommand

completion_dict = ({
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
    active_refs: int = 0
    active_rules: int = 0

    @staticmethod
    def bottom_toolbar():
        text = f'Active Refs = {Toolbar.active_refs} | Active Rules = {Toolbar.active_rules}'
        return [('class:bottom-toolbar', f'entries = {text}')]


style = Style.from_dict({
    'bottom-toolbar': '#ffffff bg:#333333',
})

bindings = KeyBindings()


def get_help() -> str:
    text = """
    {rule}              Add Rule to current engine
    .                   increments the state of the engine, then prints the active references
    .{n}                increments the state of the engine n times then prints the active references
    +{name}	            activates the named reference
    +{name}={value}	    activates the named reference with the provided value
    explore {n}	        conducts an exploration of n iterations and prints the distribution of outcomes
    ?                   prints the current engine context
    ?{name}             prints the state of the named reference
    quit                exits the environment
    help                shows the list of commands
    """
    return text


def format_data_for_cli_output(response, interior=True) -> str:
    match response:
        case str():
            result = response
        case dict() | EngineContext():
            results = []
            for k, v in response.items():
                k_out = format_data_for_cli_output(k)
                v_out = format_data_for_cli_output(v)
                if v_out:
                    results.append(f'{k_out} :: {v_out}')
            result = '\n'.join(results)
        case v1, v2:
            v1_str = format_data_for_cli_output(v1)
            v2_str = format_data_for_cli_output(v2)
            result = f'{v1_str} → {v2_str}'
        case set() | frozenset():
            results = map(format_data_for_cli_output, response)
            delimiter = ',' if interior else '\n'
            results_str = delimiter.join(results)
            result = f'{{{results_str}}}' if interior else results_str
        case list():
            results = map(format_data_for_cli_output, response)
            results_str = ','.join(results)
            result = f'[{results_str}]'
        case Reference():
            result = response.name
        case RuleExpression():
            result = str(response)
        case MPLEntity():
            if response.value:
                contents = format_data_for_cli_output(response.value)
                result = f'Entity({contents})'
            else:
                result = ''
        case _:
            result = str(response)
    return result


def execute_command(engine: MPLEngine, command: str):
    result = CommandParsers.command.parse(command)
    value = result.value
    match value:
        case SystemCommand.QUIT:
            return value
        case SystemCommand.HELP:
            return get_help()
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
            engine.tick(value.number)
            end_context = engine.context
            result = start_context.get_diff(end_context)
            return result
        case ExploreCommand() as explore_command:
            # TODO: explore command
            return 'NOT IMPLEMENTED'
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
        'auto_suggest': AutoSuggestFromHistory(),
        'validator': validator,
        'style': style,
        'key_bindings': bindings,
        'bottom_toolbar': Toolbar.bottom_toolbar,
    }
    engine = MPLEngine()

    while True:
        Toolbar.active_refs = len(engine.context.active)
        Toolbar.active_rules = len(engine.rule_interpreters)
        ref_names = set(engine.context.ref_names)
        completion_dict['+'] = ref_names
        completion_dict['?'] = ref_names
        completer = NestedCompleter.from_nested_dict(completion_dict)
        prompt_kwargs['completer'] = completer
        command = session.prompt('>  ', **prompt_kwargs)
        command_result = execute_command(engine, command)
        if command_result == SystemCommand.QUIT:
            return
        output = format_data_for_cli_output(command_result, False)
        print(output)


if __name__ == '__main__':
    run_interactive_session()
