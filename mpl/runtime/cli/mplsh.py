import os
from functools import reduce
from typing import Tuple, Any, Dict

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
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.conflict_resolution import identify_conflicts, resolve_conflict_map
from mpl.interpreter.expression_evaluation.engine_context import EngineContext

from mpl.interpreter.reference_resolution.mpl_ontology import process_machine_file
from mpl.interpreter.rule_evaluation import RuleInterpreter
from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.runtime.cli.command_parser import CommandParsers, SystemCommand, TickCommand, ExploreCommand, QueryCommand, \
    ActivateCommand, LoadCommand, AddRuleCommand, ClearCommand, MemoryType, DropRuleCommand, SaveCommand


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
    {rule}              Immediately Executes Rule Once
    add {rule}          Adds Rule to the current engine
    clear context       Clears the context of the engine
    clear rules         Clears all rules from the engine
    clear all           Clears all the data in the engine
    .                   increments the state of the engine, then prints the active references
    .{n}                increments the state of the engine n times then prints the active references
    +{name}             activates the named reference
    -{name}             deactivates the named reference
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
        case MPLEngine() as engine:
            expressions = [x.expression for x in response.rule_interpreters]
            result = map(format_data_for_cli_output, expressions)
            result = list(sorted(result))
            rules = '\n'.join(result)
            context = format_data_for_cli_output(response.context)
            return f'{rules}\n---\n{context}'
        case EntityValue():
            if response.value:
                contents = format_data_for_cli_output(response.value)
                result = f'Entity({contents})'
            else:
                result = ''
        case _:
            result = str(response)
    return result


def execute_command(engine: MPLEngine, command: str) -> MPLEngine | str | SystemCommand | Dict:
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
            interpreter = RuleInterpreter.from_expression(value)
            context = EngineContext.from_references(interpreter.references)
            engine.context = context | engine.context
            result = engine.execute_interpreters({interpreter})
            return result
        case AddRuleCommand():
            engine = engine.add(value.expression)
            return f'Incorporated Rule: {value.expression}'
        case DropRuleCommand():
            engine.remove(value.expression)
            return f'Dropped Rule: {value.expression}'
        case LoadCommand(path, MemoryType.CONTEXT):
            new_context, _ = process_machine_file(path)
            engine.context |= new_context
            return engine
        case LoadCommand(path, MemoryType.RULES):
            new_engine = MPLEngine.from_file(path)
            new_engine.context |= engine.context
            return new_engine
        case LoadCommand(path, MemoryType.ALL):
            engine = MPLEngine.from_file(path)
            return engine
        case SaveCommand():
            value.save(engine)
        case TickCommand():
            start_context = engine.context
            result = engine.tick(value.number)
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
                    result = engine.active
                    return result
        case ClearCommand():
            match value.memory_type:
                case MemoryType.CONTEXT:
                    contexts = [EngineContext.from_interpreter(x) for x in engine.rule_interpreters]
                    engine.context = reduce(EngineContext.__or__, contexts)
                    return engine
                case MemoryType.RULES:
                    new_engine = MPLEngine()
                    new_engine.context = engine.context
                    return new_engine
                case MemoryType.ALL:
                    return MPLEngine()

        case ActivateCommand() as activate_command:
            re = RuleExpression((activate_command.expression,), tuple())
            interpreter = RuleInterpreter.from_expression(re)
            rule_context = EngineContext.from_interpreter(interpreter)
            engine.context = rule_context | engine.context
            results = engine.execute_interpreters(frozenset({interpreter}))
            return results
        case _:
            return f'Unknown command: {value}'


def run_interactive_session():
    history_path = f'{os.path.expanduser("~")}/.mplsh_history'
    our_history = FileHistory(history_path)
    session = PromptSession(history=our_history)
    completion_dict = {
        'clear': {
            'context',
            'rules',
            'all',
        },
        'add': None,
        'help': None,
        'quit': None,
        'explore': None,
    }

    prompt_kwargs = {
        'auto_suggest': AutoSuggestFromHistory(),
        'validator': validator,
        'style': style,
        'key_bindings': bindings,
        'bottom_toolbar': Toolbar.bottom_toolbar,
        'complete_while_typing': True,
    }
    engine = MPLEngine()

    while True:
        Toolbar.active_refs = len(engine.context.active)
        Toolbar.active_rules = len(engine.rule_interpreters)
        ref_names = set(engine.context.ref_names)
        ref_names = dict([(x, None) for x in ref_names])

        adjustments = {
            '+': ref_names,
            '-': ref_names,
            '?': ref_names,
        }

        completion_dict |= adjustments
        completer = NestedCompleter.from_nested_dict(completion_dict)
        prompt_kwargs['completer'] = completer
        command = session.prompt('>  ', **prompt_kwargs)
        command_result = execute_command(engine, command)
        match command_result:
            case MPLEngine():
                engine = command_result
            case SystemCommand.QUIT:
                return
        output = format_data_for_cli_output(command_result, False)
        print(output)


if __name__ == '__main__':
    run_interactive_session()
