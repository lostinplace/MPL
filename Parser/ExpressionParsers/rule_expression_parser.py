from dataclasses import dataclass
from typing import Union, List, Optional

from parsita import TextParsers, fwd, longest

from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpressionParsers as asexp, AssignmentExpression
from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers as aexp, ArithmeticExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, LogicalExpressionParsers as lexp
from Parser.ExpressionParsers.state_expression_parser import StateExpression, StateExpressionParsers as sexp
from Parser.Tokenizers.operator_tokenizers import StateOperator, MPLOperator, LogicalOperatorParsers as lop, MPLOperatorParsers as mops\

from lib.custom_parsers import repsep2, SeparatedList, debug, check, back


@dataclass(frozen=True, order=True)
class RuleClause:
    type: str
    expression: Union[StateExpression, LogicalExpression, AssignmentExpression, ArithmeticExpression]


@dataclass(frozen=True, order=True)
class Rule:
    clauses: List[RuleClause]
    operators: List[MPLOperator]


def to_clause(clause_type):
    def result_func(parser_output):
        return RuleClause(clause_type, parser_output)
    return result_func


def interpret_simple_expression(parser_results: SeparatedList):
    operands = parser_results
    operators = parser_results.separators

    result = Rule(operands, operators)
    return result


def db_cb(parser, reader):
    pass


class RuleExpressionParsers(TextParsers):

    trigger_operand = longest(sexp.expression | lexp.expression)

    trigger_clause = (back(mops.trigger_on_the_right_operator) >> trigger_operand) | \
                     (trigger_operand << check(mops.trigger_on_the_left_operator)) > to_clause('trigger')

    query_clause = back(mops.query_operator) >> lexp.expression > to_clause('query')

    state_clause = (back(mops.state_on_the_right_operator) >> sexp.expression) | \
                   sexp.expression << check(mops.state_on_the_left_operator) |\
                   sexp.expression > to_clause('state')

    action_clause = back(mops.action_operator) >> asexp.expression > to_clause('action')

    scenario_clause = back(mops.scenario_operator) >> aexp.expression > to_clause('scenario')

    any_clause = longest(trigger_clause, query_clause, action_clause, scenario_clause, state_clause)

    expression = repsep2(any_clause, mops.operator, min=2) > interpret_simple_expression
