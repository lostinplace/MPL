from dataclasses import dataclass
from typing import Set, Dict, Tuple, Any, Iterable, FrozenSet, Optional

from networkx import MultiDiGraph

from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.conflict_resolution import identify_conflicts, resolve_conflicts
from mpl.interpreter.expression_evaluation.engine_context import EngineContext, context_diff

from mpl.interpreter.reference_resolution.mpl_ontology import process_machine_file, rule_expressions_from_graph, \
    construct_graph_from_expressions
from mpl.interpreter.rule_evaluation import RuleInterpreter, RuleInterpretationState, RuleInterpretation
from mpl.lib import fs
from mpl.lib.graph_operations import combine_graphs, drop_from_graph


@dataclass(order=True)
class MPLEngine:
    rule_interpreters: Set[RuleInterpreter] = frozenset()
    context: EngineContext = EngineContext()
    history: Tuple[context_diff, ...] = ()
    graph: Optional[MultiDiGraph] = MultiDiGraph()

    @staticmethod
    def from_file(file: str | MachineFile) -> 'MPLEngine':
        if isinstance(file, str):
            file = MachineFile.from_file(file)

        context, graph = process_machine_file(file)
        rule_expressions = rule_expressions_from_graph(graph)
        interpreters = {RuleInterpreter.from_expression(rule) for rule in rule_expressions}
        return MPLEngine(interpreters, context, (), graph)

    def add(self, rules: RuleExpression | Set[RuleExpression], inplace=True) -> 'MPLEngine':

        if not isinstance(rules, Iterable):
            rules = {rules}

        new_graph = construct_graph_from_expressions(rules)
        graph = combine_graphs(self.graph, new_graph)
        context = EngineContext.from_graph(graph) | self.context
        interpreters = {RuleInterpreter.from_expression(rule) for rule in rules} | self.rule_interpreters

        if inplace:
            self.context = context
            self.rule_interpreters = interpreters
            self.graph = graph
            return self

        return MPLEngine(interpreters, context, self.history, graph)

    def remove(self, rules: RuleExpression | Set[RuleExpression], inplace=True) -> 'MPLEngine':
        if not isinstance(rules, Iterable):
            rules = {rules}

        new_interpreters = {interpreter for interpreter in self.rule_interpreters if interpreter.expression not in rules}
        expressions = {interpreter.expression for interpreter in new_interpreters}
        new_graph = drop_from_graph(expressions, self.graph)

        if inplace:
            self.rule_interpreters = new_interpreters
            self.graph = new_graph
            return self

        return MPLEngine(new_interpreters, self.context, self.history, new_graph)

    def execute_expression(self, expression: RuleExpression) -> Dict[str, Tuple[Any, Any]]:
        original_context = self.context
        interpreter = RuleInterpreter.from_expression(expression)
        result = interpreter.interpret(self.context)
        if result.state != RuleInterpretationState.APPLICABLE:
            return dict()
        conflicts = identify_conflicts({result})
        resolved = resolve_conflicts(conflicts)
        self.apply(resolved)
        output = original_context.get_diff(self.context)
        self.history = (output,) + self.history
        return output

    def execute_interpreters(self, interpreters: Set[RuleInterpreter]) -> Dict[str, Tuple[Any, Any]]:
        original_context = self.context
        interpretations = {interpreter.interpret(self.context) for interpreter in interpreters}
        applicable = {x for x in interpretations if x.state == RuleInterpretationState.APPLICABLE}
        if not applicable:
            return dict()
        conflicts = identify_conflicts(applicable)
        resolved = resolve_conflicts(conflicts)
        self.apply(resolved)
        output = original_context.get_diff(self.context)
        return output

    def apply(self, interpretations: FrozenSet[RuleInterpretation]):
        original_context = self.context
        new_context = self.context.apply(interpretations)
        self.context = new_context
        return original_context.get_diff(self.context)

    def tick(self, count: int = 1) -> Dict[str, Tuple[Any, Any]]:
        original_context = self.context
        output = dict()
        if count > 0:
            #  tick forward
            for tick in range(count):
                self.execute_interpreters(self.rule_interpreters)
            output = original_context.get_diff(self.context)
            self.history = (output,) + self.history
        elif count < 0:
            # tick backward
            for tick in range(abs(count)):
                this_tick = self.history[0]
                self.history = self.history[1:]
                resolved = MPLEngine.invert_diff(this_tick)
                self.apply(resolved)
            output = original_context.get_diff(self.context)

        return output

    @staticmethod
    def invert_diff(diff: context_diff) -> FrozenSet[RuleInterpretation]:
        from mpl.interpreter.expression_evaluation.entity_value import EntityValue

        diff_change = dict()
        diff_descriptors = list()
        for key, diff_item in diff.items():
            key = Reference(key)
            diff_change[key] = EntityValue.from_value(diff_item[0])
            descriptor = f'{key}::{diff_item[1]}→{diff_item[0]}'
            diff_descriptors.append(descriptor)
        name = ';'.join(diff_descriptors)
        interpretation = RuleInterpretation(RuleInterpretationState.APPLICABLE, diff_change, name)
        return fs(interpretation)

    def activate(self, ref: Reference | Set[Reference],  value: Any = None) -> context_diff:
        old_context = self.context
        new_context = old_context.activate(ref, value)
        self.context = new_context
        return old_context.get_diff(new_context)

    def deactivate(self, ref: Reference | Set[Reference]) -> context_diff:
        old_context = self.context
        new_context = old_context.deactivate(ref)
        self.context = new_context
        return old_context.get_diff(new_context)

    def query(self, ref: Reference):
        from mpl.interpreter.expression_evaluation.entity_value import EntityValue

        value = self.context.get(ref)
        match value:
            case EntityValue():
                return value.value
            case _:
                return value

    @property
    def active(self) -> Dict[Reference, FrozenSet]:
        return self.context.active

    def __hash__(self):
        context_set = frozenset(self.context.items())
        edges = self.graph.edges(data='relationship')
        edges_as_set = frozenset(edges)
        return hash((context_set, frozenset(self.rule_interpreters), edges_as_set, self.history))

