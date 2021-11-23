from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Sequence, Union, Tuple, Any, List
from parsita import Parser, lit, TextParsers
from parsita.state import Input, Output, Continue, Reader

from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression, Negation
from Parser.ExpressionParsers.reference_expression_parser import DeclarationExpression, Reference, ReferenceExpression
from Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleClause
from Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from Parser.ExpressionParsers.state_expression_parser import StateExpression
from Parser.ExpressionParsers.trigger_expression_parser import TriggerExpression
from Parser.Tokenizers.operator_tokenizers import MPLOperator
from lib.additive_parsers import TrackedValue
from lib.repsep2 import SeparatedList
from lib.simple_graph import SimpleGraph


@dataclass(frozen=True, order=True)
class DefinitionTreeNode:
    definition_expression: RuleExpression | DeclarationExpression | TrackedValue
    parent: DefinitionTreeNode
    children: Tuple[RuleExpression | DeclarationExpression | 'DefinitionTreeNode']


def consume(self, reader: Reader[Input]):
    """
    This is left here for posterity, it's the old 'tree parser'
    :param self:
    :param reader:
    :return:
    """
    status = self.parser.consume(reader)
    if not isinstance(status, Continue):
        return status

    output = []
    current_depth = 0
    current_node: DefinitionTreeNode = None

    result: TrackedValue
    status.value: SeparatedList

    for result in status.value:
        if not isinstance(result, TrackedValue):
            continue
        this_line_depth = result.metadata.start

        if this_line_depth == 0:
            if current_node:
                while current_node.parent is not None:
                    current_node = current_node.parent
                output.append(current_node)
            this_node = DefinitionTreeNode(result, None, [])
        elif this_line_depth > current_depth:
            this_node = DefinitionTreeNode(result, current_node, [])
            current_node.children.append(this_node)
        elif this_line_depth == current_depth:
            this_node = DefinitionTreeNode(result, current_node.parent, [])
            this_node.parent.children.append(this_node)
        elif this_line_depth < current_depth:
            while current_node.definition_expression.metadata.start > this_line_depth:
                current_node = current_node.parent
            this_node = DefinitionTreeNode(result, current_node.parent, [])
            this_node.parent.children.append(this_node)
        current_node = this_node
        current_depth = this_line_depth

    while current_node.parent is not None:
        current_node = current_node.parent

    output = output + [current_node]
    status.value = tuple(output)
    return status


#TODO: Unify Arithmetic expression and State expression
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
    clauses: Tuple[MPLClause]
    operators: Tuple[MPLOperator]


@dataclass(frozen=True, order=True)
class MPLClause:
    id: int
    expression: StateExpression | LogicalExpression | AssignmentExpression | ArithmeticExpression


class MPLEntityClass(Enum):
    MACHINE = 0
    STATE = 1
    VARIABLE = 2
    TRIGGER = 3


class MPLValueType(Enum):
    ANY = 0
    NUMBER = 1
    ENTITY = 2
    STRING = 3
    

class MPLGraphEdgeType(Enum):
    DEFINED_BY         = 0
    QUALIFIED_BY       = 1 << 0
    INSTANTIATED_AS    = 1 << 1
    CHILD_OF           = 1 << 2
    EXCLUSIVE_CHILD_OF = 1 << 3
    EVALUATED_IN       = 1 << 4
    CHANGED_IN         = 1 << 5


# TODO: add block operator  a -| b
# TODO: Observations create novel "Observation" values without consuming the value of the previous clause
# TODO: collecting from multiple sources combines their values, neeed to figure out extrication of values from a collection
# TODO: MPL CLauses should track an MPLLine for just their source


@dataclass(frozen=True, order=True)
class MPLEntity:
    id: int
    name: str
    entity_class: MPLEntityClass
    value_type: MPLValueType | str
    value: str


def get_entity_id(line: MPLLine, *args) -> int:
    other = '-SALT_COMBINE-'.join(map(repr, args))
    input = repr(line) + other
    return hash(input)


def reference_to_simple_graph(ref: Reference) -> SimpleGraph:
    out_verts = set([ref])
    out_edges = set()

    if ref.type:
        simple_ref = Reference(ref.name, None)
        out_verts.add(simple_ref)
        out_edges.add((simple_ref, MPLGraphEdgeType.QUALIFIED_BY, ref))
    return SimpleGraph(out_verts, out_edges)


def declaration_expression_to_simple_graph(
        expression: DeclarationExpression | TrackedValue,
        line_number: int
) -> SimpleGraph:
    line = MPLLine(line_number, expression.metadata.start, expression.metadata.source)
    result = reference_to_simple_graph(expression.reference)
    for v in result.vertices:
        result.edges.add((v, MPLGraphEdgeType.DEFINED_BY, line))
    result.vertices.add(line)

    entity_id = get_entity_id(line)

    match expression.reference.type:
        case 'machine':
            entity_class = MPLEntityClass.MACHINE
            value_type = MPLValueType.ANY
        case 'state':
            entity_class = MPLEntityClass.STATE
            value_type = MPLValueType.ANY
        case value:
            entity_class = MPLEntityClass.VARIABLE
            value_type = value or MPLValueType.ANY

    entity = MPLEntity(entity_id, expression.reference.name, entity_class, value_type, None)
    result.vertices.add(entity)
    result.edges.add((expression.reference, MPLGraphEdgeType.INSTANTIATED_AS, entity))

    return result, entity_class, value_type


def rule_expression_to_simple_graph(
        expression: RuleExpression | TrackedValue,
        line_number: int
):
    result = SimpleGraph()
    line = MPLLine(line_number, expression.metadata.start, expression.metadata.source)
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

        this_operator:MPLOperator = i < len(operators) and operators[i]
        consumable_references = SimpleGraph()
        if isinstance(this_expression, StateExpression) and \
                this_operator and \
                this_operator.behavior == 'CONSUME':
            consumable_references = complex_expression_to_reference_graph(clause.expression, include_negations=False)
        elif isinstance(this_expression, AssignmentExpression):
            consumable_references = SimpleGraph(set([this_expression.lhs.value]))
        changed_in_edges = set([(v, MPLGraphEdgeType.CHANGED_IN, this_clause) for v in consumable_references.vertices])
        refgraph.edges |= changed_in_edges

        if isinstance(clause.expression, StateExpression):
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

    return result


#TODO: This is garbage still
class MPLGraphConversionParser(Generic[Input, Output], Parser[Input, Sequence[Output]]):
    def __init__(self, parser: Parser[Input, Output]):
        super().__init__()
        self.parser = parser

    def consume(self, reader: Reader[Input]):
        status = self.parser.consume(reader)
        if not isinstance(status, Continue):
            return status

        output = []
        current_depth = 0
        current_id = 0
        line_number = 1
        current_node: DefinitionTreeNode = None

        result: TrackedValue
        status.value: SeparatedList[str | DeclarationExpression | RuleExpression ]


        """
        parsing rules:
        
        each line increments the line number
        
        on empty string we continue
        
        at depth = 0 we add directly to the output without parent
        
        at depth > current we add the last observed (item, depth) to the lineage, and start adding child relationships 
        to the last observed at current depth
        
        at depth < current, we drop the items in the lineage until we hit the new depth.  we then process the item as 
        a child of the latest in the lineage
        
        
        
        on declaration expression, we have to establish a few things
            base reference
            qualified reference
            
            in the event that the parent is a state, we can assume that any declaration expression is a state, we can
            also establish the "exclusive child" relationship
        
        
        if the current lineage has a parent, the last thing wee do is establish the parent relationship
        
        """

        for result in status.value:
            if not isinstance(result, TrackedValue):
                continue
            this_line_depth = result.metadata.start

            if this_line_depth == 0:
                if current_node:
                    while current_node.parent is not None:
                        current_node = current_node.parent
                    output.append(current_node)
                this_node = DefinitionTreeNode(result, None, [])
            elif this_line_depth > current_depth:
                this_node = DefinitionTreeNode(result, current_node, [])
                current_node.children.append(this_node)
            elif this_line_depth == current_depth:
                this_node = DefinitionTreeNode(result, current_node.parent, [])
                this_node.parent.children.append(this_node)
            elif this_line_depth < current_depth:
                while current_node.definition_expression.metadata.start > this_line_depth:
                    current_node = current_node.parent
                this_node = DefinitionTreeNode(result, current_node.parent, [])
                this_node.parent.children.append(this_node)
            current_node = this_node
            current_depth = this_line_depth

        while current_node.parent is not None:
            current_node = current_node.parent

        output = output + [current_node]
        status.value = tuple(output)
        return status

    def __repr__(self):
        return self.name_or_nothing() + f"tree({repr(self.parser)})"


def complex_expression_to_reference_graph(
        expr: ArithmeticExpression | LogicalExpression | StateExpression | ScenarioExpression | AssignmentExpression,
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

    for operand in expr.operands:
        if isinstance(operand, ReferenceExpression):
            out |= reference_to_simple_graph(operand.value)
        elif isinstance(operand, (ArithmeticExpression, StateExpression, LogicalExpression)):
            out |= complex_expression_to_reference_graph(operand)
        elif isinstance(operand, TriggerExpression):
            out |= reference_to_simple_graph(operand.name.value)
        elif isinstance(operand, Negation):
            tmp = operand
            while isinstance(tmp, Negation):
                tmp = tmp.operand
            if isinstance(tmp, ReferenceExpression) and include_negations:
                out |= reference_to_simple_graph(tmp.value)
            else:
                out |= complex_expression_to_reference_graph(operand)
    return out