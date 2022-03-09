from dataclasses import dataclass
from itertools import zip_longest
from typing import Tuple

from parsita import TextParsers, longest, pred, opt

from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpressionParsers as AsExP, \
    AssignmentExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpressionParsers as ScExP, \
    ScenarioExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression, QueryExpressionParsers as LExP
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpression
from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperator, MPLOperatorParsers as MOPs
from mpl.lib.parsers.additive_parsers import track
from mpl.lib.parsers.custom_parsers import back
from mpl.lib.parsers.repsep2 import repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class RuleClause:
    type: str
    expression: QueryExpression | AssignmentExpression | ScenarioExpression | TriggerExpression

    def __str__(self):
        return str(self.expression)



@dataclass(frozen=True, order=True)
class RuleExpression:
    clauses: Tuple[RuleClause, ...]
    operators: Tuple[MPLOperator, ...]

    def __str__(self):
        result = ''
        for clause, operator in zip_longest(self.clauses, self.operators):
            operator_str = ''
            if operator:
                operator_str = f' {operator} '
            clause_str = str(clause.expression)
            result += f'{clause_str}{operator_str}'
        return result



def to_clause(clause_type):
    def result_func(parser_output):
        return RuleClause(clause_type, parser_output)
    return result_func


def interpret_simple_expression(parser_results: SeparatedList) -> RuleExpression:
    operands = tuple(parser_results.__iter__())
    operators = parser_results.separators

    result = RuleExpression(operands, operators)
    return result


def is_scenario_compatible(parser_result):
    if not parser_result:
        return True
    return parser_result[0].RHType == 'STATE'


class RuleExpressionParsers(TextParsers, whitespace=r'[ \t]*'):

    query_clause = LExP.expression > to_clause('query')

    prior_operator = opt(back(MOPs.operator))

    scenario_clause = pred(prior_operator, is_scenario_compatible, 'is_scenario_compatible') \
                      >> ScExP.expression > to_clause('scenario')

    action_clause = opt(back(MOPs.action_operator)) >> AsExP.expression > to_clause('action')

    any_clause = track(longest(action_clause, scenario_clause, query_clause))

    expression = repsep2(any_clause, MOPs.operator, min=1) > interpret_simple_expression
