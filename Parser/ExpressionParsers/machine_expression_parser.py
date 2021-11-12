from __future__ import annotations

from dataclasses import dataclass

from typing import Optional, List, Union, Tuple

from parsita import TextParsers, reg, opt, longest

from Parser.ExpressionParsers.reference_expression_parser import ReferenceExpression, \
    ReferenceExpressionParsers as RefExP, DeclarationExpression
from Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleExpressionParsers as RuleExP

from lib.additive_parsers import track
from lib.custom_parsers import check
from lib.tree_parser import tree, DefinitionTreeNode
from lib.repsep2 import repsep2


@dataclass(frozen=True, order=True)
class StateDefinitionExpression:
    name: str
    rules: List[DeclarationExpression | RuleExpression]


@dataclass(frozen=True, order=True)
class MachineDefinitionExpression:
    name: str
    rules: List[
        RuleExpression | DeclarationExpression | 'MachineDefinitionExpression'
    ]


def get_definition(rule_expression: RuleExpression) -> Optional[Tuple[str, str]]:
    if len(rule_expression.clauses) != 1:
        return None
    sole_clause = rule_expression.clauses[0]
    if sole_clause.type != 'state':
        return None

    if len(sole_clause.expression.operands) != 1:
        return None

    sole_operand:ReferenceExpression = sole_clause.expression.operands[0]
    if not isinstance(sole_operand, ReferenceExpression):
        return None

    reference = sole_operand.value
    ref_name, ref_type = reference.name, reference.type.content

    if ref_type not in {'machine', 'state'} :
        return None

    return ref_name, ref_type


def compact_tree(a_tree: DefinitionTreeNode):
    def_expression: RuleExpression = a_tree.definition_expression
    definition = get_definition(def_expression)
    if definition == 'state':
        pass


class MachineDefinitionExpressionParsers(TextParsers, whitespace=None):
    ignored_whitespace = reg(r"[ \t]*")
    iw = ignored_whitespace

    rule_line = iw >> track(RuleExP.expression) << iw
    declaration_line = iw >> track(RefExP.declaration_expression) << iw
    empty_line = iw & check('\n')
    valid_line = longest(empty_line, declaration_line, rule_line)
    rule_lines = repsep2(valid_line, '\n', reset=True, min=1)
    machine_file = tree(rule_lines)

