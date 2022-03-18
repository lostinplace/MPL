from dataclasses import dataclass
from itertools import zip_longest
from typing import Tuple, FrozenSet, Optional

from parsita import TextParsers, longest, opt

from mpl.Parser.ExpressionParsers import Expression
from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpressionParsers as AsExP, \
    AssignmentExpression
from mpl.Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, Reference
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpressionParsers as ScExP, \
    ScenarioExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression, QueryExpressionParsers as QExP
from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperator, MPLOperatorParsers as MOPs
from mpl.lib.parsers.additive_parsers import track
from mpl.lib.parsers.custom_parsers import back
from mpl.lib.parsers.repsep2 import repsep2, SeparatedList


@dataclass(frozen=True, order=True)
class RuleExpression(Expression):
    clauses: Tuple[QueryExpression | AssignmentExpression | ScenarioExpression, ...]
    operators: Tuple[MPLOperator, ...]
    parent: Optional[ReferenceExpression] = None

    def __str__(self):
        result = ''
        for clause, operator in zip_longest(self.clauses, self.operators):
            operator_str = ''
            if operator:
                operator_str = f' {operator} '
            clause_str = str(clause)
            result += f'{clause_str}{operator_str}'
        if self.parent:
            result += f' in {self.parent}'
        return result

    def __repr__(self):
        return f'RuleExpression({self.clauses}, {self.operators})'

    @staticmethod
    def interpret(parser_results: SeparatedList) -> 'RuleExpression':
        operands = tuple(parser_results.__iter__())
        operators = parser_results.separators

        result = RuleExpression(operands, operators)
        return result

    def qualify(self, context: Tuple[str, ...], ignore_types: bool = False) -> 'RuleExpression':
        clauses = tuple(clause.qualify(context, ignore_types) for clause in self.clauses)
        return RuleExpression(
            clauses=clauses,
            operators=self.operators
        )

    @property
    def reference_expressions(self) -> FrozenSet[ReferenceExpression]:
        result = frozenset()
        for clause in self.clauses:
            result |= clause.reference_expressions
        return result


class RuleExpressionParsers(TextParsers, whitespace=r'[ \t]*'):

    query_clause = QExP.expression

    prior_operator = opt(back(MOPs.operator))

    scenario_clause = ScExP.expression

    action_clause = opt(back(MOPs.action_operator)) >> AsExP.expression

    any_clause = track(longest(action_clause, scenario_clause, query_clause))

    expression = repsep2(any_clause, MOPs.operator, min=1) > RuleExpression.interpret
