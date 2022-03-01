from __future__ import annotations

import dataclasses
import enum
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from numbers import Number
from typing import Tuple, List, Any, FrozenSet, Union, Optional

from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression, Negation
from mpl.Parser.ExpressionParsers.reference_expression_parser import DeclarationExpression, Reference, \
    ReferenceExpression
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleClause
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.Parser.ExpressionParsers.state_expression_parser import StateExpression
from mpl.Parser.ExpressionParsers.trigger_expression_parser import TriggerExpression
from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperator
from mpl.Parser.Tokenizers.simple_value_tokenizer import StringToken
from mpl.lib.parsers.additive_parsers import TrackedValue
from mpl.lib.quick_filter_set import filter_set
from mpl.lib.parsers.repsep2 import SeparatedList
from mpl.lib.simple_graph import SimpleGraph
from sympy import Expr


@dataclass(frozen=True, order=True)
class DefinitionTreeNode:
    definition_expression: RuleExpression | DeclarationExpression | TrackedValue
    parent: DefinitionTreeNode
    children: Tuple[RuleExpression | DeclarationExpression | 'DefinitionTreeNode']


#TODO: parser clause types should be enum
#TODO: MPL operator values should be enum


@dataclass(frozen=True, order=True)
class MPLLine:
    line_number: int
    depth: int
    source: str


@dataclass(frozen=True, order=True)
class MPLRule:
    id: int
    clauses: Tuple[MPLClause, ...]
    operators: Tuple[MPLOperator, ...]


@dataclass(frozen=True, order=True)
class MPLClause:
    id: int
    expression: QueryExpression | AssignmentExpression | ScenarioExpression


class MPLEntityClass(enum.Flag):
    MACHINE = enum.auto()
    STATE = enum.auto()
    VARIABLE = enum.auto()
    TRIGGER = enum.auto()
    CLEARED_BY_CONSUMPTION = MACHINE | STATE | TRIGGER
    

class MPLGraphEdgeType(enum.Flag):
    DEFINED_BY = enum.auto()
    QUALIFIED_BY = enum.auto()
    INSTANTIATED_AS = enum.auto()
    CHILD_OF = enum.auto()
    EXCLUSIVE_CHILD_OF = enum.auto()
    EVALUATED_IN = enum.auto()
    CHANGED_IN = enum.auto()


# TODO: add block operator  a -| b
# TODO: Observations create novel "Observation" values without consuming the value of the previous clause
# TODO: collecting from multiple sources combines their values, neeed to figure out extrication of values from a collection
# TODO: MPL Clauses should track an MPLLine for just their source


EntityValue = FrozenSet[Union[Number, Expr, bool, str]]


@dataclass(frozen=True, order=True)
class MPLEntity:
    id: int
    name: str
    entity_class: MPLEntityClass
    value: Optional[FrozenSet[Expr | Number | str]]

    def __add__(self, other):
        pass


def get_entity_id(line: MPLLine, *args) -> int:
    # TODO: rework entity ids, the resolver system should be unaware of them until the end
    other = '-SALT_COMBINE-'.join(map(repr, args))
    input = repr(line) + other
    return hash(input)


def reference_to_simple_graph(ref: Reference) -> SimpleGraph:
    out_verts = set([ref])
    out_edges = set()

    if ref.type:
        simple_ref = dataclasses.replace(ref, type=None)
        out_verts.add(simple_ref)
        out_edges.add((simple_ref, MPLGraphEdgeType.QUALIFIED_BY, ref))

    return SimpleGraph(out_verts, out_edges)


def complex_expression_to_reference_graph(
        expr: ArithmeticExpression | QueryExpression | StateExpression | ScenarioExpression | AssignmentExpression,
        include_negations=True
):
    out = SimpleGraph()

    match expr:
        case ScenarioExpression(value):
            return complex_expression_to_reference_graph(value)
        case AssignmentExpression(lhs, rhs, _):
            lhs: ReferenceExpression
            out.vertices.add(lhs.value)
            return out | complex_expression_to_reference_graph(rhs)
        case StringToken(_):
            return out

    for operand in expr.operands:
        if isinstance(operand, ReferenceExpression):
            out |= reference_to_simple_graph(operand.value)
        elif isinstance(operand, (ArithmeticExpression, StateExpression, QueryExpression)):
            out |= complex_expression_to_reference_graph(operand)
        elif isinstance(operand, TriggerExpression):
            out |= reference_to_simple_graph(operand.name)
        elif isinstance(operand, Negation):
            tmp = operand
            while isinstance(tmp, Negation):
                tmp = tmp.operand
            if isinstance(tmp, ReferenceExpression) and include_negations:
                out |= reference_to_simple_graph(tmp.value)
            else:
                out |= complex_expression_to_reference_graph(operand)
    return out


def expression_with_metadata_to_mpl_line(expr: RuleExpression | DeclarationExpression | TrackedValue, line_number) -> MPLLine:
    return MPLLine(line_number, expr.metadata.start, expr.metadata.source)


def declaration_expression_to_simple_graph(
        expression: DeclarationExpression | TrackedValue,
        mpl_line: MPLLine
) -> Tuple[SimpleGraph, MPLEntityClass]:

    #TODO:  this is a hack, we assumme that untyped declarations are states
    ref = expression.reference
    if not ref.type:
        ref = dataclasses.replace(ref, type='state')

    result = reference_to_simple_graph(ref)
    for v in result.vertices:
        result.edges.add((v, MPLGraphEdgeType.DEFINED_BY, mpl_line))
    result.vertices.add(mpl_line)

    entity_id = get_entity_id(mpl_line)

    match ref.type:
        case 'machine':
            entity_class = MPLEntityClass.MACHINE
        case 'state':
            entity_class = MPLEntityClass.STATE
        case value:
            entity_class = MPLEntityClass.VARIABLE

    entity = MPLEntity(entity_id, ref.name, entity_class, None)
    result.vertices.add(entity)
    result.edges.add((ref, MPLGraphEdgeType.INSTANTIATED_AS, entity))

    return result, entity_class


def rule_expression_to_simple_graph(
        expression: RuleExpression | TrackedValue,
        line: MPLLine
    ) -> Tuple[SimpleGraph, MPLRule]:

    result = SimpleGraph()
    result.vertices.add(line)
    rightmost_state_clause: MPLClause = None
    rule_id = get_entity_id(line)
    operators = expression.operators
    out_clauses: List[MPLClause] = []

    """
    a ref is evaluated in a clause when:
        it is in the clause's refgraph
    
    a ref is changed in a clause when:
        the right operator consumes from a state expression and it is not negated
        
        the ref is the lhs of an assignment expression
         
        the ref is found in the rightmost state expression in the rule, and it is not negated
    """

    clause: RuleClause
    for i, clause in enumerate(expression.clauses):
        clause_id = get_entity_id(line, i)
        this_expression = clause.expression
        this_clause: MPLClause = MPLClause(clause_id, clause.expression)
        out_clauses.append(this_clause)

        refgraph = complex_expression_to_reference_graph(clause.expression)
        evaluated_in_edges = set([(v, MPLGraphEdgeType.EVALUATED_IN, this_clause) for v in refgraph.vertices])
        refgraph.edges |= evaluated_in_edges

        this_operator: MPLOperator = i < len(operators) and operators[i]
        consumable_references = SimpleGraph()

        if isinstance(this_expression, QueryExpression) and \
                this_operator and \
                this_operator.behavior == 'CONSUME':
            consumable_references = complex_expression_to_reference_graph(clause.expression, include_negations=False)
        elif isinstance(this_expression, AssignmentExpression):
            consumable_references = SimpleGraph(set([this_expression.lhs.value]))
        changed_in_edges = set([(v, MPLGraphEdgeType.CHANGED_IN, this_clause) for v in consumable_references.vertices])
        refgraph.edges |= changed_in_edges

        if isinstance(this_expression, QueryExpression):
            rightmost_state_clause = this_clause

        refgraph.vertices.add(this_clause)
        result |= refgraph

    if rightmost_state_clause and out_clauses.index(rightmost_state_clause):
        consumable_references = complex_expression_to_reference_graph(
            rightmost_state_clause.expression,
            include_negations=False
        )
        changed_in_edges = \
            set([(v, MPLGraphEdgeType.CHANGED_IN, rightmost_state_clause) for v in consumable_references.vertices])
        result.edges |= changed_in_edges

    rule = MPLRule(rule_id, tuple(out_clauses), tuple(operators))
    result.vertices.add(rule)

    for clause in out_clauses:
        result.vertices.add(clause)
        result.edges.add((clause, MPLGraphEdgeType.CHILD_OF, rule))

    return result, rule


def mpl_file_lines_to_simple_graph(expresssions: SeparatedList(str | DeclarationExpression | RuleExpression | TrackedValue)):
    out_graph = SimpleGraph()
    open_nodes: List[Tuple[Reference, int]] = []
    current_depth = 0

    for index, expression in enumerate(expresssions):
        if not isinstance(expression, TrackedValue):
            continue
        mpl_line: MPLLine = expression_with_metadata_to_mpl_line(expression, index + 1)
        this_line_depth = expression.metadata.start
        parent: Reference
        result_graph: SimpleGraph
        result_node: Reference | MPLRule = None

        # identify parent
        if this_line_depth > current_depth:
            parent = open_nodes[-1][0] if len(open_nodes) else None
        elif this_line_depth == current_depth:
            parent = open_nodes[-2][0] if len(open_nodes) > 1 else None
        elif this_line_depth < current_depth:
            filtered_nodes = filter(lambda x: x[1] <= this_line_depth, open_nodes)
            open_nodes = list(filtered_nodes)
            parent = open_nodes[-2][0] if len(open_nodes) > 1 else None

        if isinstance(expression, DeclarationExpression):
            result_node, result_graph = get_graph_for_declaration_expression(mpl_line, expression)
        elif isinstance(expression, RuleExpression):
            result_graph, result_node = rule_expression_to_simple_graph(expression, mpl_line)

        if parent:
            child_edge = (result_node, MPLGraphEdgeType.CHILD_OF, parent)
            result_graph.edges.add(child_edge)

        if parent and isinstance(parent, Reference) and parent.type == 'state' and isinstance(result_node, Reference):
            child_edge = (result_node, MPLGraphEdgeType.EXCLUSIVE_CHILD_OF, parent)
            result_graph.edges.add(child_edge)

        # update lineage
        new_node = (result_node, this_line_depth)
        if this_line_depth > current_depth:
            open_nodes += [new_node]
        elif this_line_depth <= current_depth:
            open_nodes = open_nodes[:-1] + [new_node]

        current_depth = this_line_depth

        out_graph |= result_graph

    out_graph = process_unqualified_references(out_graph)

    out_graph = process_uninstantiated_references(out_graph)

    return out_graph


def process_unqualified_references(graph: SimpleGraph) -> SimpleGraph:
    reference_verts = filter_set(graph.vertices, Reference(Any, None))
    qualification_edges = filter_set(graph.edges, (Reference, MPLGraphEdgeType.QUALIFIED_BY, Reference))
    qualified_verts = {x[0] for x in qualification_edges}

    unqualified_verts = reference_verts ^ qualified_verts
    unqualified_verts.discard(Reference('void', None))

    if not unqualified_verts:
        return graph

    evaluation_edges = filter_set(graph.edges, (unqualified_verts, MPLGraphEdgeType.EVALUATED_IN, MPLClause))
    evaluation_clauses_dict = defaultdict(list)
    for ee in evaluation_edges:
        evaluation_clauses_dict[ee[0]].append(ee[2])

    vert_intersection = evaluation_clauses_dict.keys() & unqualified_verts
    if not vert_intersection:
        names = [x.name for x in vert_intersection]
        names_as_string = ', '.join(names)
        raise NotImplementedError(f'could not infer types for the following refernces: {names_as_string}')

    #TODO: Operators should resolve to comparable flags to make this less silly
    vert: Reference
    for vert in unqualified_verts:
        tmp_ref = dataclasses.replace(vert, type='any')
        graph.vertices.add(tmp_ref)
        graph.edges.add((vert, MPLGraphEdgeType.QUALIFIED_BY, tmp_ref))
        evaluated_in_edges = graph.filter((vert, MPLGraphEdgeType.EVALUATED_IN, Any))
        changed_in_edges = graph.filter((vert, MPLGraphEdgeType.CHANGED_IN, Any))
        new_evaluation_edges = [(tmp_ref, x[1],  x[2]) for x in evaluated_in_edges | changed_in_edges]
        graph.edges |= set(new_evaluation_edges)

        #TODO: I'm going to punt on this for now, and any undefined ref is going to be 'any' (yikes)

    # cleanup untyped references with edges invoking changes
    untyped_reference_changes = graph.filter(
        (Reference(str, None), MPLGraphEdgeType.CHANGED_IN, Any)
    )

    qualification_edges = graph.filter(
        (Reference(str, None), MPLGraphEdgeType.QUALIFIED_BY, Reference)
    )
    qualification_map = dict([(x[0], x[2]) for x in qualification_edges])

    for change in untyped_reference_changes:
        new_ref = qualification_map.get(change[0])
        if not new_ref:
            continue
        tmp = (new_ref, MPLGraphEdgeType.CHANGED_IN, change[2])
        graph.edges.add(tmp)

    return graph


def get_graph_for_declaration_expression(line: MPLLine, expression: DeclarationExpression) \
        -> Tuple[Reference, SimpleGraph]:

    result, entity_class = declaration_expression_to_simple_graph(expression, line)
    qualified_refs = filter_set(result.vertices, Reference(str, str))

    return next(iter(qualified_refs)), result


def instantiate_reference(ref:Reference) -> MPLEntity:
    entity_class: MPLEntityClass

    match ref.type:
        case 'state':
            entity_class = MPLEntityClass.STATE
        case 'machine':
            entity_class = MPLEntityClass.MACHINE
        case 'trigger':
            entity_class = MPLEntityClass.TRIGGER
        case 'string':
            entity_class = MPLEntityClass.VARIABLE
        case 'number':
            entity_class = MPLEntityClass.VARIABLE
        case _:
            entity_class = MPLEntityClass.VARIABLE

    id = get_entity_id(ref)
    entity = MPLEntity(id, ref.name, entity_class, None)
    return entity


def process_uninstantiated_references(graph: SimpleGraph) -> SimpleGraph:
    all_qualified_refs = graph.filter(Reference(str, str))
    all_instantiated_edges = graph.filter((Reference, MPLGraphEdgeType.INSTANTIATED_AS, Any))
    all_instantiated_refs = set([x[0] for x in all_instantiated_edges])
    uninstantiated_refs = all_qualified_refs ^ all_instantiated_refs

    for ref in uninstantiated_refs:
        entity = instantiate_reference(ref)
        graph.vertices.add(entity)
        graph.edges.add((ref, MPLGraphEdgeType.INSTANTIATED_AS, entity))

    return graph







