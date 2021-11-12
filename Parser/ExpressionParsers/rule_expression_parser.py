from dataclasses import dataclass
from typing import Union, List, Optional

from parsita import TextParsers, fwd, longest, pred, opt

from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpressionParsers as AsExP, AssignmentExpression
from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpressionParsers as AExP, ArithmeticExpression
from Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpressionParsers as ScExP
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, LogicalExpressionParsers as LExP
from Parser.ExpressionParsers.state_expression_parser import StateExpression, StateExpressionParsers as SExP
from Parser.Tokenizers.operator_tokenizers import MPLOperator, MPLOperatorParsers as MOPs
from lib.custom_parsers import debug, check, back
from lib.repsep2 import repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class RuleClause:
    type: str
    expression: Union[StateExpression, LogicalExpression, AssignmentExpression, ArithmeticExpression]


@dataclass(frozen=True, order=True)
class RuleExpression:
    clauses: List[RuleClause]
    operators: List[MPLOperator]


def to_clause(clause_type):
    def result_func(parser_output):
        return RuleClause(clause_type, parser_output)
    return result_func


def interpret_simple_expression(parser_results: SeparatedList):
    operands = parser_results
    operators = parser_results.separators

    result = RuleExpression(operands, operators)
    return result


def is_scenario_compatible(parser_result):
    if not parser_result:
        return True
    return parser_result[0].RHType == 'STATE'


class RuleExpressionParsers(TextParsers, whitespace=r'[ \t]*'):

    state_clause = SExP.expression > to_clause('state')

    query_clause = (back(MOPs.state_operator) >> LExP.expression) | (LExP.expression << check(MOPs.state_operator)) \
                   > to_clause('query')

    prior_operator = opt(back(MOPs.operator))

    scenario_clause = pred(prior_operator, is_scenario_compatible, 'is_scenario_compatible') \
                      >> ScExP.expression > to_clause('scenario')

    action_clause = back(MOPs.action_operator) >> AsExP.expression > to_clause('action')

    any_clause = longest(state_clause, query_clause, action_clause, scenario_clause)

    expression = repsep2(any_clause, MOPs.operator, min=1) > interpret_simple_expression
