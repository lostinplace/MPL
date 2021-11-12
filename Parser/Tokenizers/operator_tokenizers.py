from dataclasses import dataclass
from typing import Optional

from parsita import TextParsers, lit, opt, rep, success, reg, longest
from parsita.util import splat

from lib.custom_parsers import debug
from lib.additive_parsers import track, TrackedValue


@dataclass(frozen=True, order=True)
class MPLOperator:
    LHType: Optional[str]
    behavior: str
    RHType: str
    depth: int


S = {
    'ANY': None,
    'FORK': '|',
    "CONSUME": '-',
    "OBSERVE": '~',
    'STATE': '>',
    'ACTION': '@'
}

s_inverted = dict(map(reversed, S.items()))


def interpret_operator(result: TrackedValue):
    lhs, middle, rhs = result
    lhs = lhs and lhs[0] or None
    lhs_out = s_inverted[lhs]
    middle_out = s_inverted[middle]
    rhs_out = s_inverted[rhs]
    result = MPLOperator(lhs_out, middle_out, rhs_out, result.metadata.start)
    return result


iw = reg(r'[ \t]*')


class MPLOperatorParsers(TextParsers, whitespace=None):
    lhs = lit(S['FORK'])
    middle = lit(S['CONSUME']) | S['OBSERVE']
    rhs = lit(S['STATE']) | S['ACTION']

    action_operator = iw >> opt(lhs) & middle & '@' << iw

    fork_operator = iw >> S['FORK'] & middle & rhs << iw

    state_operator = iw >> opt(lhs) & middle & '>' << iw

    any_operator = longest(
        action_operator,
        state_operator,
        fork_operator
    )

    operator = iw >> track(any_operator) << iw > interpret_operator


@dataclass(frozen=True, order=True)
class StateOperator:
    contents: str


class StateOperatorParsers(TextParsers, whitespace=None):
    and_state = lit('&') > StateOperator
    or_state = lit('|') > StateOperator

    not_state = lit('!') > StateOperator

    operator = iw >> (and_state | or_state) << iw


@dataclass(frozen=True, order=True)
class LogicalOperator:
    contents: str


class LogicalOperatorParsers(TextParsers, whitespace=None):
    logical_negation = lit('!') > LogicalOperator

    logical_and = lit('&&') > LogicalOperator
    logical_or = lit('||') > LogicalOperator
    logical_equals = lit('==') > LogicalOperator
    logical_not_equals = lit('!=') > LogicalOperator
    logical_gt = lit('>') > LogicalOperator
    logical_gte = lit('>=') > LogicalOperator
    logical_lt = lit('<') > LogicalOperator
    logical_lte = lit('<=') > LogicalOperator

    all_operators = longest(
        logical_and, logical_or, logical_equals, logical_not_equals, logical_gt, logical_gte, logical_lt, logical_lte
    )

    operator = iw >> all_operators << iw


@dataclass(frozen=True, order=True)
class ArithmeticOperator:
    contents: str


class ArithmeticOperatorParsers(TextParsers, whitespace=None):
    arith_add = lit('+') > ArithmeticOperator
    arith_subtract = lit('-') > ArithmeticOperator
    arith_multiply = lit('*') > ArithmeticOperator
    arith_divide = lit('/') > ArithmeticOperator
    arith_exponent = lit('^') > ArithmeticOperator
    arith_modulus = lit('%') > ArithmeticOperator

    operator = iw >> (arith_add | arith_subtract | arith_multiply | arith_divide | arith_exponent | arith_modulus) << iw


@dataclass(frozen=True, order=True)
class AssignmentOperator:
    contents: str


class AssignmentOperatorParsers(TextParsers, whitespace=None):
    assign_direct = lit('=') > AssignmentOperator
    assign_increment = lit('+=') > AssignmentOperator
    assign_decrement = lit('-=') > AssignmentOperator
    assign_multiply = lit('*=') > AssignmentOperator
    assign_divide = lit('/=') > AssignmentOperator

    operator = iw >> (assign_direct | assign_increment | assign_decrement | assign_multiply | assign_divide) << iw
