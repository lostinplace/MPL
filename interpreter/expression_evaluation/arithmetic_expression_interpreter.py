from numbers import Number
from operator import itemgetter
from typing import Collection, Dict, List

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference
from Parser.Tokenizers.simple_value_tokenizer import NumberToken
from ast import literal_eval

from interpreter.reference_resolution.reference_graph_resolution import MPLEntity

order_of_operations_value = {
    '^': 2,
    '*': 1,
    '/': 1,
    '%': 1,
    '+': 0,
    '-': 0,
}


def get_postfix_operand(operand):
    if isinstance(operand, ArithmeticExpression):
        return postfix(operand)
    elif isinstance(operand, NumberToken):
        return literal_eval(operand.content)
    elif isinstance(operand, ReferenceExpression):
        return operand.value


def combine_output(output: List, item: Number | Collection) -> List:
    result = output
    if isinstance(item, Collection):
        result += item
    else:
        result.append(item)
    return result


def flat_append(out: List, operand: Number|Reference|List):
    if isinstance(operand, Collection):
        out += operand
    else:
        out.append(operand)
    return out


def postfix(expression: ArithmeticExpression):
    # TODO: Arithmetic expressions can also include logical expressions for some reason, should fix that
    out = []
    stack = []
    operand = get_postfix_operand(expression.operands[0])
    flat_append(out, operand)

    for i, operator in enumerate(expression.operators):
        operator_value = order_of_operations_value[operator.contents]
        while stack and stack[-1][1] >= operator_value:
            out.append(stack.pop()[0])
        stack.append((operator.contents, operator_value))
        operand = expression.operands[i + 1]
        operand = get_postfix_operand(operand)
        flat_append(out, operand)

    out += map(itemgetter(0), reversed(stack))
    return out


evaluation_operations = {
    '+': lambda x,y: x + y,
    '-': lambda x,y: x - y,
    '*': lambda x,y: x * y,
    '/': lambda x,y: x / y,
    # TODO: replace ^ with **
    '^': lambda x,y: x ** y,
    '%': lambda x,y: x % y,
}


def eval_postfix(postfix_queue: List[Number | Reference | str], ref_cache: Dict[Reference, Number | str | MPLEntity]):
    index = 0
    while index < len(postfix_queue):
        item = postfix_queue[index]
        if isinstance(item, Reference):
            value = ref_cache[item]
            if not isinstance(value, Number):
                message = f"Arithmetic expressions only support numeric values at this time, " \
                          f"the value of {repr(item)} was {repr(value)}"
                raise NotImplementedError(message)
            postfix_queue[index] = value
        elif item in evaluation_operations:
            operation = evaluation_operations[item]
            x = postfix_queue[index - 2]
            y = postfix_queue[index - 1]
            value = operation(x, y)
            postfix_queue[index] = value
            del postfix_queue[index-2:index]
            index -= 2
        else:
            index += 1
    assert len(postfix_queue) == 1
    return postfix_queue[0]


def evaluate_expression(expression: ArithmeticExpression, reference_cache: Dict[Reference, Number | str | MPLEntity]) -> Number:
    postfix_queue = postfix(expression)
    result = eval_postfix(postfix_queue, reference_cache)
    return result
