from dataclasses import replace, dataclass
from typing import Any, Dict, Iterator

from parsita import Failure, Success

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression, ArithmeticExpressionParsers
from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpressionParsers, AssignmentExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, LogicalExpressionParsers
from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpressionParsers, ReferenceExpression
from Parser.ExpressionParsers.state_expression_parser import StateExpressionParsers, StateExpression
from Parser.Tokenizers.operator_tokenizers import ArithmeticOperator
from Parser.Tokenizers.simple_value_tokenizer import NumberToken


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
}


def quick_parse(out_type: type, value: str):
    parser = parser_map[out_type]
    result = parser.parse(value)
    return result.value
