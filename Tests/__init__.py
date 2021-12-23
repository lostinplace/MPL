from dataclasses import replace, dataclass
from typing import Any, Dict, Iterator, Generic, TypeVar

from parsita import Failure, Success

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression, ArithmeticExpressionParsers
from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpressionParsers, AssignmentExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, LogicalExpressionParsers
from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpressionParsers, ReferenceExpression, \
    DeclarationExpression
from Parser.ExpressionParsers.rule_expression_parser import RuleExpressionParsers, RuleExpression
from Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression, ScenarioExpressionParsers
from Parser.ExpressionParsers.state_expression_parser import StateExpressionParsers, StateExpression
from Parser.ExpressionParsers.trigger_expression_parser import TriggerExpressionParsers, TriggerExpression
from Parser.Tokenizers.simple_value_tokenizer import NumberToken, SimpleValueTokenizers, StringToken


@dataclass(frozen=True, order=True)
class ParseResult:
    parser_input: str
    expected: Any
    actual: Any

    def as_strings(self) -> 'ParseResult':
        expected = nest_string(self.expected)
        actual = nest_string(self.actual)
        return ParseResult(self.parser_input, f"{self.parser_input}\n---\n{expected}", f"{self.parser_input}\n---\n{actual}")


def nest_string(source: Any):
    if not isinstance(source, str):
        source = str(source)
    result = ''
    tab_depth = 0
    for char in source:
        if char in {'(', '['}:
            result += '\n'
            tab_depth += 1
            result += '--' * tab_depth
            result += char
        elif char in {')', ']'}:

            result += '\n'
            result += '--' * tab_depth
            result += char
            tab_depth -= 1
        else:
            result += char
    return result


def collect_parsing_expectations(expectations: Dict[str, Any], parser) -> Iterator[ParseResult]:
    """

    :param expectations:
    :param parser:
    :return: yields actual then expected, then the input as strings
    """
    for (parser_input, expected_outcome) in expectations.items():
        actual_result = parser.parse(parser_input)

        if expected_outcome is Failure:
            assert type(actual_result) is Failure
            continue
        if type(actual_result) == Failure:
            pass
        result = ParseResult(parser_input, Success(expected_outcome), actual_result)
        yield result


def qdae(value):
    return quick_parse(ArithmeticExpression, value)


def qre(value):
    return quick_parse(ReferenceExpression, value)


def qse(value):
    return quick_parse(StateExpression, value)


def qase(value):
    return quick_parse(AssignmentExpression, value)


parser_map ={
    AssignmentExpression: AssignmentExpressionParsers.expression,
    StateExpression: StateExpressionParsers.expression,
    ReferenceExpression: ReferenceExpressionParsers.expression,
    ArithmeticExpression: ArithmeticExpressionParsers.expression,
    LogicalExpression: LogicalExpressionParsers.expression,
    TriggerExpression: TriggerExpressionParsers.expression,
    ScenarioExpression: ScenarioExpressionParsers.expression,
    RuleExpression: RuleExpressionParsers.expression,
    DeclarationExpression: ReferenceExpressionParsers.declaration_expression,
    StringToken: SimpleValueTokenizers.string_token,
}


T = TypeVar('T')


def quick_parse(out_type: Generic[T], value: str) -> T:
    parser = parser_map[out_type]
    result = parser.parse(value)
    assert isinstance(result, Success)
    return result.value
