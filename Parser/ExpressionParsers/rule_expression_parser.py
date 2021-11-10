from dataclasses import dataclass
from typing import Union, List, Optional

from parsita import TextParsers, fwd, longest

from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpressionParsers as aexp, AssignmentExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, LogicalExpressionParsers as lexp
from Parser.ExpressionParsers.state_expression_parser import StateExpression, StateExpressionParsers as sexp
from Parser.Tokenizers.operator_tokenizers import StateOperator, MPLOperator, LogicalOperatorParsers as lop, MPLOperatorParsers as mops\

from lib.custom_parsers import repsep2, SeparatedList, debug, check, back


@dataclass(frozen=True, order=True)
class Rule:
    operands: List[Union[StateExpression, LogicalExpression, AssignmentExpression]]
    operators: List[MPLOperator]


def interpret_simple_expression(parser_results: SeparatedList):
    operands = parser_results
    operators = parser_results.separators

    result = LogicalExpression(operands, operators)
    return result


def db_cb(parser, reader):
    pass


class RuleExpressionParsers(TextParsers):
    trigger_clause = (sexp.expression << check(mops.left_trigger_operator)) | \
                     (back(mops.right_trigger_operator) >> sexp.expression)

    query_clause = back(mops.query_operator) >> lexp.expression

    state_clause = sexp.expression << check(mops.right_state_operator) | \
                   (back(mops.left_state_operator) >> sexp.expression)

    action_clause = back(mops.action_operator)

    simple_rule_expression = fwd()
    parenthesized_simple_expression = '(' >> simple_rule_expression << ')'

    trigger_clause = sexp.expression & check(mops.right_trigger_operator) | check(mops.left_trigger_operator) & sexp.expression
    query_clause = check(mops.query_operator)

    negated_expression = fwd()
    logical_expression_operand = longest(
        parenthesized_simple_expression, \
        negated_expression, \
        lexp.expression, \
        aexp.expression
    )

    simple_rule_expression.define(
        repsep2(logical_expression_operand, lop.operator, min=1) > interpret_simple_expression
    )

    expression = simple_rule_expression
