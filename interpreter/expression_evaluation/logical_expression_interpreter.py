from dataclasses import dataclass
from numbers import Number
from operator import itemgetter
from typing import Collection, Dict, List, Any, Callable, Type, Union

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression
from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference
from Parser.Tokenizers.simple_value_tokenizer import NumberToken, StringToken
from ast import literal_eval

from Tests import quick_parse
from interpreter.reference_resolution.reference_graph_resolution import MPLEntity, MPLEntityClass, MPLValueType


@dataclass(frozen=True, order=True)
class OperatorOperation:
    symbol: str
    score: int
    allowed_types: Type
    method: Callable[[Any, Any], Any]


operations = [
    # TODO: Replace ^ with ** and include xor
    OperatorOperation('^', 6, Number, lambda x, y: x ** y),
    OperatorOperation('*', 5, Number, lambda x, y: x * y),
    OperatorOperation('/', 5, Number, lambda x, y: x / y),
    OperatorOperation('%', 5, Number, lambda x, y: x % y),
    OperatorOperation('+', 4, Number, lambda x, y: x + y),
    OperatorOperation('-', 4, Number, lambda x, y: x - y),
    OperatorOperation('&&',  2, Any, lambda x, y: x and y),
    OperatorOperation('||',  1, Any, lambda x, y: x or y),
    OperatorOperation('==',  0, Any, lambda x, y: x == y),
    OperatorOperation('!=',  0, Any, lambda x, y: x != y),
    OperatorOperation('>',  0, Any, lambda x, y: x > y),
    OperatorOperation('>=',  0, Any, lambda x, y: x >= y),
    OperatorOperation('<',  0, Any, lambda x, y: x < y),
    OperatorOperation('<=',  0, Any, lambda x, y: x <= y),
]

op_dict = dict([(x.symbol, x) for x in operations])


def get_postfix_operand(operand):
    from ..expression_evaluation import arithmetic_expression_interpreter as ArExI

    if isinstance(operand, ArithmeticExpression):
        return postfix(operand)
    if isinstance(operand, LogicalExpression):
        return postfix(operand)
    elif isinstance(operand, NumberToken):
        return literal_eval(operand.content)
    elif isinstance(operand, StringToken):
        return operand.content
    elif isinstance(operand, ReferenceExpression):
        return operand.value


def combine_output(output: List, item: str | Number | Collection) -> List:
    result = output
    if isinstance(item, Collection):
        result += item
    else:
        result.append(item)
    return result


def flat_append(out: List, operand: str | Number | Reference | List):
    if isinstance(operand, Collection):
        out += operand
    else:
        out.append(operand)
    return out


def postfix(expression: LogicalExpression | ArithmeticExpression):
    out = []
    stack = []
    operand = get_postfix_operand(expression.operands[0])
    flat_append(out, operand)

    for i, operator in enumerate(expression.operators):
        operator_value = op_dict[operator.contents].score
        while stack and stack[-1][1] >= operator_value:
            out.append(stack.pop()[0])
        stack.append((operator.contents, operator_value))
        operand = expression.operands[i + 1]
        operand = get_postfix_operand(operand)
        flat_append(out, operand)

    out += map(itemgetter(0), reversed(stack))
    return out


def is_operation_suitable(operation, x, y):
    if operation.allowed_types is Any:
        return True
    flag = isinstance(x, operation.allowed_types)
    flag &= isinstance(y, operation.allowed_types)
    return flag


def eval_postfix(postfix_queue: List[Number | Reference | str], ref_cache: Dict[Reference, Number | str | MPLEntity]):
    index = 0
    while index < len(postfix_queue):
        item = postfix_queue[index]
        if isinstance(item, Reference):
            value = ref_cache[item]
            postfix_queue[index] = value
        elif item in op_dict:
            operation = op_dict[item]
            x = postfix_queue[index - 2]
            y = postfix_queue[index - 1]
            if not is_operation_suitable(operation, x, y):
                op_name = operation.symbol
                x_name = f'{repr(x)}:{repr(type(x))}'
                y_name = f'{repr(x)}:{repr(type(x))}'
                raise NotImplementedError(rf'Cannot execute operation {op_name} for values {x_name} and {y_name}')
            value = operation.method(x, y)
            postfix_queue[index] = value
            del postfix_queue[index-2:index]
            index -= 2
        else:
            index += 1
    assert len(postfix_queue) == 1
    return postfix_queue[0]


def evaluate_expression(expression: LogicalExpression, reference_cache: Dict[Reference, Number | str | MPLEntity]) -> Any:
    postfix_queue = postfix(expression)
    result = eval_postfix(postfix_queue, reference_cache)
    return result


def test_expression_evaluation():

    cache = {
        Reference('test', None): 7,
        Reference('test 2', None): 196,
    }

    expectations = {
        '4+3*8^2/32+4^3/4-7': 19,
        '1+(test-3)*4': 17,
        '9- 4 + -5.12 * (test 2 ^ 0.5 + 7) / test': -10.36,
    }

    for input, expected in expectations.items():
        expr = quick_parse(ArithmeticExpression, input)
        postfix_queue = postfix(expr)
        actual = eval_postfix(postfix_queue, cache)
        assert actual == expected


def test_postfix_conversion():
    expectations = {
        '4+3*8^2/32+4^3/4-7': [
            4, 3, 8, 2, '^', '*', 32, '/', '+', 4, 3, '^', 4, '/', '+', 7, '-'
        ],
        '1+(test-3)*4': [
            1, Reference('test', None), 3, '-', 4, '*', '+'
        ],

    }

    for input, expected in expectations.items():
        expr = quick_parse(ArithmeticExpression, input)
        actual = postfix(expr)
        assert actual == expected


def test_expression_evaluation():
    cache = {
        Reference('x', None): 5,
        Reference('y', None): 7,
        Reference('a', None): 3,
        Reference('c', None): 12,
        Reference('d', None): None,
    }

    expectations = {
        "2^((-1+6)/4)*7/-9/3": -0.6166259114828924,
        '3*x^2 + (5^y + (a+19) -c) ^ 3': 477020287110450,
        '12.0/-13^14.15--16': (16.000000000000004-9.417368741536094e-16j),
        '-149.012': -149.012,
        '-149.012': -149.012,
        'a && d': None,
        'd || (a + c == y - -8)': True
    }

    for input, expected in expectations.items():
        expr = quick_parse(LogicalExpression, input)
        actual = evaluate_expression(expr, cache)
        a = "⚡"

        assert actual == expected