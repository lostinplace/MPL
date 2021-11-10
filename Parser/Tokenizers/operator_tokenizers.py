from dataclasses import dataclass
from typing import Optional

from parsita import TextParsers, lit, opt, rep, success
from parsita.util import splat

from lib.custom_parsers import track


@dataclass(frozen=True, order=True)
class MPLOperator:
    LHType: Optional[str]
    behavior: str
    RHType: str
    depth: int


S = {
    'ANY': None,
    'EVENT': '*',
    'STATE': '>',
    'ACTION': '@',
    'FORK': '|',
    "CONSUME": '-',
    "OBSERVE": '~',
    "QUERY": '?',
}

s_inverted = dict(map(reversed, S.items()))


def interpret_operator(result):
    lhs, middle, rhs = result.value
    lhs = lhs and lhs[0] or None
    lhs_out = s_inverted[lhs]
    middle_out = s_inverted[middle]
    rhs_out = s_inverted[rhs]
    result = MPLOperator(lhs_out, middle_out, rhs_out, result.start)
    return result


class MPLOperatorParsers(TextParsers, whitespace=None):
    ignored_whitespace = rep(lit(" ") | '\t')

    lhs = lit(S['EVENT']) | S['FORK']
    middle = lit(S['CONSUME']) | S['OBSERVE']
    rhs = lit(S['STATE']) | S['EVENT'] | S['ACTION'] | S['QUERY']

    left_trigger_operator = '*' & middle & rhs
    right_trigger_operator = opt(lhs) & middle & '*'
    trigger_operator = left_trigger_operator | right_trigger_operator

    action_operator = opt(lhs) & middle & '@'

    left_state_operator = success(None) & middle & '>'
    right_state_operator = opt(lhs) & middle & '>'
    state_operator = left_state_operator | right_state_operator

    query_operator = opt(lhs) & middle & '?'

    fork_operator = '|' & middle & rhs

    any_operator = trigger_operator | action_operator | state_operator | query_operator | fork_operator

    operator = ignored_whitespace >> track(any_operator) << ignored_whitespace > interpret_operator


@dataclass(frozen=True, order=True)
class StateOperator:
    contents: str


class StateOperatorParsers(TextParsers):
    and_state = lit('&') > StateOperator
    or_state = lit('|') > StateOperator

    not_state = lit('!') > StateOperator

    operator = and_state | or_state


@dataclass(frozen=True, order=True)
class LogicalOperator:
    contents: str


class LogicalOperatorParsers(TextParsers):
    logical_negation = lit('!') > LogicalOperator

    logical_and = lit('&&') > LogicalOperator
    logical_or = lit('||') > LogicalOperator
    logical_equals = lit('==') > LogicalOperator
    logical_not_equals = lit('!=') > LogicalOperator
    logical_gt = lit('>') > LogicalOperator
    logical_gte = lit('>=') > LogicalOperator
    logical_lt = lit('<') > LogicalOperator
    logical_lte = lit('<=') > LogicalOperator

    operator = logical_and | logical_or | logical_equals | logical_not_equals | logical_gt | \
               logical_gte | logical_lt | logical_lte


@dataclass(frozen=True, order=True)
class ArithmeticOperator:
    contents: str


class ArithmeticOperatorParsers(TextParsers):
    arith_add = lit('+') > ArithmeticOperator
    arith_subtract = lit('-') > ArithmeticOperator
    arith_multiply = lit('*') > ArithmeticOperator
    arith_divide = lit('/') > ArithmeticOperator
    arith_exponent = lit('^') > ArithmeticOperator
    arith_modulus = lit('%') > ArithmeticOperator

    operator = arith_add | arith_subtract | arith_multiply | arith_divide | arith_exponent | arith_modulus


@dataclass(frozen=True, order=True)
class AssignmentOperator:
    contents: str


class AssignmentOperatorParsers(TextParsers):
    assign_direct = lit('=') > AssignmentOperator
    assign_increment = lit('+=') > AssignmentOperator
    assign_decrement = lit('-=') > AssignmentOperator
    assign_multiply = lit('*=') > AssignmentOperator
    assign_divide = lit('/=') > AssignmentOperator

    operator = assign_direct | assign_increment | assign_decrement | assign_multiply | assign_divide
