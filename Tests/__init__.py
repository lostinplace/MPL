from dataclasses import replace
from typing import Any, Dict

from parsita import Failure, Success

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticOperation, ArithmeticExpression
from Parser.ExpressionParsers.label_expression_parser import LabelExpression, LabelExpressionParsers
from Parser.Tokenizers.operator_tokenizers import ArithmeticOperator
from Parser.Tokenizers.simple_value_tokenizer import NumberToken, LabelToken, SimpleValueTokenizers


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


def assert_parsing_expectations(expectations: Dict[str, Any], parser):
    results = []
    for (v, expected_outcome) in expectations.items():
        result = parser.parse(v)

        if expected_outcome is Failure:
            assert type(result) is Failure
            continue
        if type(result) == Failure:
            breakpoint()
            pass
        assert type(result) == Success

        result_str = nest_string(result)
        expected_str = nest_string(Success(expected_outcome))

        assert result_str == expected_str
        results.append((v, expected_outcome, result))
    return results


def collect_parsing_expectations(expectations: Dict[str, Any], parser):
    """

    :param expectations:
    :param parser:
    :return: yields actual then expected, then the input as strings
    """
    for (input, expected_outcome) in expectations.items():
        actual_result = parser.parse(input)

        if expected_outcome is Failure:
            assert type(actual_result) is Failure
            continue
        if type(actual_result) == Failure:
            breakpoint()
            pass
        assert type(actual_result) == Success

        actual_result_str = nest_string(actual_result)
        expected_str = nest_string(Success(expected_outcome))
        yield actual_result_str, expected_str, input


def qdae(*args):
    """
    quick define arithmetic expression

    a helper method for defining expectations
    :param args:
    :return:
    """
    results = []
    for arg in args:
        operand = arg
        operator = None

        if isinstance(arg, tuple):
            operand = arg[0]
            operator = ArithmeticOperator(arg[1])

            if isinstance(operand, tuple):
                operand = qdae(*arg)
                operator = None

        if isinstance(operand, (int, float)):
            operand = NumberToken(str(operand))

        tmp = ArithmeticOperation(operand, operator)
        results.append(tmp)
    result = ArithmeticExpression(results)
    return result


def qle(input, depth:int = None):
    result = LabelExpressionParsers.expression.parse(input).value
    # TODO:  this only goes to depth of 1
    if depth is not None:
        result = replace(result, depth=depth)
        result_parent = result.parent
        if result_parent is not None:
            parent_depth = result.parent.depth
            result_parent = replace(result.parent, depth=parent_depth + depth)
            result = replace(result, parent=result_parent)

    return result
