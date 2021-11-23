from __future__ import annotations

from typing import Optional

import networkx as nx

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, Negation
from Parser.ExpressionParsers.reference_expression_parser import DeclarationExpression, ReferenceExpression, Reference
from Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleClause
from Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from Parser.ExpressionParsers.state_expression_parser import StateExpression
from Parser.Tokenizers.operator_tokenizers import MPLOperator
from lib.simple_graph import SimpleGraph
from lib.tree_parser import DefinitionTreeNode
from enum import Enum

G = nx.DiGraph()


class ResolverGraphEdgeTypes(Enum):
    DESCRIBED_BY = 'described by'
    INSTANTIATED_AS = 'instantiated as'
    EVALUATED_IN = 'evaluated in clause'
    CHILD_OF = 'child of'
    ASSIGNED_IN = 'assigned in'
    CONSUMED_IN = 'consumed in'


def complex_expression_to_reference_graph(
        expr: ArithmeticExpression | LogicalExpression | StateExpression | ScenarioExpression,
        include_negations = True
):
    out = SimpleGraph()

    if isinstance(expr, ScenarioExpression):
        return complex_expression_to_reference_graph(expr.value)

    for operand in expr.operands:
        if isinstance(operand, ReferenceExpression):
            out |= reference_to_simple_graph(operand.value)
        elif isinstance(operand, (ArithmeticExpression, StateExpression, LogicalExpression)):
            out |= complex_expression_to_reference_graph(operand)
        elif isinstance(operand, Negation):
            tmp = operand
            while isinstance(tmp, Negation):
                tmp = tmp.operand
            if isinstance(tmp, ReferenceExpression) and include_negations:
                out |= reference_to_simple_graph(tmp.value)
            else:
                out |= complex_expression_to_reference_graph(operand)
    return out


class MPLMachine:
    name: str
    active: bool = False

    def __init__(self, name):
        self.name = name


class MPLState:
    name: str
    active: bool = False

    def __init__(self, name):
        self.name = name


def reference_to_simple_graph(ref: Reference):
    rge = ResolverGraphEdgeTypes
    out_verts = set([ref])
    out_edges = set()

    if ref.type:
        simple_ref = Reference(ref.name, None)
        out_verts.add(simple_ref)
        out_edges = set([(simple_ref, rge.DESCRIBED_BY, ref)])
    return SimpleGraph(out_verts, out_edges)


def action_clause_to_refgraph(clause: RuleClause):
    rge = ResolverGraphEdgeTypes

    expr: AssignmentExpression = clause.expression
    target_ref = expr.lhs.value
    target_refgraph = reference_to_simple_graph(target_ref)
    tmp = SimpleGraph([clause], [(target_ref, rge.ASSIGNED_IN, clause)])
    out = target_refgraph | tmp

    source_expr = expr.rhs
    source_refgraph = complex_expression_to_reference_graph(source_expr)
    out |= source_refgraph

    for ref in source_refgraph.vertices:
        out.edges.add((ref, rge.EVALUATED_IN, clause))

    return out


def expression_clause_to_refgraph(clause: RuleClause):
    rge = ResolverGraphEdgeTypes

    expr = clause.expression
    out = complex_expression_to_reference_graph(expr)

    for ref in out.vertices:
        out.edges.add((ref, rge.EVALUATED_IN, clause))

    out.vertices.add(clause)

    return out


clause_refgraph_resolvers = {
    'scenario': expression_clause_to_refgraph,
    'action': action_clause_to_refgraph,
    'state': expression_clause_to_refgraph,
    'query': expression_clause_to_refgraph,
}


def get_consummable_references(expr: StateExpression) -> SimpleGraph:
    refgraph = complex_expression_to_reference_graph(expr, False)
    return refgraph.vertices


def rule_expression_to_usegraph(expression: RuleExpression) -> SimpleGraph:
    rge = ResolverGraphEdgeTypes
    out = SimpleGraph({expression})

    for i, clause in enumerate(expression.clauses):
        tmp = expression_clause_to_refgraph(clause)
        tmp.edges.add((clause, rge.CHILD_OF, expression))

        if i < len(expression.operators):
            right_operator: MPLOperator = expression.operators[i]

            if right_operator.behavior == "CONSUME" and isinstance(clause.expression, StateExpression):
                consumed_references = get_consummable_references(clause.expression)
                for ref in consumed_references:
                    tmp.edges.add((ref, rge.CONSUMED_IN, expression))

        out |= tmp

    return out


def construct_reference_graph_from_dtn(node: DefinitionTreeNode, parent: Optional[MPLMachine | MPLState]):
    expr = node.definition_expression
    out = SimpleGraph()

    if isinstance(expr, RuleExpression):
        for clause in expr.clauses:


            # TODO: refgraph_resolvers for query, state
            # ScenarioExpression
            pass


    if isinstance(expr, DeclarationExpression):
        if expr.type == 'machine':
            this_vertex = MPLMachine(expr.name)
        elif expr.type == 'state':
            this_vertex = MPLState(expr.name)

        out.vertices.add(this_vertex)

        if parent:
            out.edges.append((this_vertex, ResolverGraphEdgeTypes.CHILD_OF, parent))

        ref_graph = reference_to_simple_graph(expr.reference)
        out |= ref_graph

        # TODO: need to finish this







    pass
