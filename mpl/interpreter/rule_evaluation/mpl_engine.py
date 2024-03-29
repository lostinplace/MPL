from dataclasses import dataclass
from random import random, randint
from typing import Set, Dict, Tuple, Any, Iterable, FrozenSet, Optional

from networkx import MultiDiGraph

from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleExpressionParsers
from mpl.interpreter.conflict_resolution import identify_conflicts, compress_interpretations, \
    resolve_conflict_map
from mpl.interpreter.expression_evaluation.engine_context import EngineContext, context_diff
from mpl.interpreter.expression_evaluation.entity_value import false_value

from mpl.interpreter.reference_resolution.mpl_ontology import process_machine_file, rule_expressions_from_graph, \
    construct_graph_from_expressions, Relationship
from mpl.interpreter.rule_evaluation import RuleInterpreter, RuleInterpretationState, RuleInterpretation, \
    create_rule_interpreter
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

    def add(self, rules: RuleExpression | Set[RuleExpression]) -> 'MPLEngine':
        if not isinstance(rules, Iterable):
            rules = {rules}

        new_graph = construct_graph_from_expressions(rules)
        self.graph = combine_graphs(self.graph, new_graph)
        new_context = EngineContext.from_graph(self.graph)
        self.context, changes = new_context.update(self.context)

        self.rule_interpreters = {RuleInterpreter.from_expression(rule) for rule in rules} | self.rule_interpreters
        return self

    def remove(self, rules: RuleExpression | Set[RuleExpression]) -> 'MPLEngine':
        if not isinstance(rules, Iterable):
            rules = {rules}

        self.rule_interpreters = \
            {interpreter for interpreter in self.rule_interpreters if interpreter.expression not in rules}
        expressions = {interpreter.expression for interpreter in self.rule_interpreters}
        self.graph = drop_from_graph(expressions, self.graph)

        return self

    def execute_expression(self, expression: RuleExpression) -> Dict[Reference, context_diff]:
        interpreter = RuleInterpreter.from_expression(expression)
        new_context = EngineContext.from_references(interpreter.references)
        all_changes = dict()
        context, changes = new_context.update(self.context)
        all_changes |= changes

        result = interpreter.interpret(context)
        if result.state != RuleInterpretationState.APPLICABLE:
            return dict()
        conflicts = identify_conflicts(fs(result))
        resolved = resolve_conflict_map(conflicts)
        resolved_changes = compress_interpretations(resolved)
        context, changes = context.update(resolved_changes)
        all_changes |= changes
        self.history = (all_changes,) + self.history
        return all_changes

    def get_invalidated_triggers(self, interpretations: FrozenSet[RuleInterpretation]) -> \
            Dict[Reference, Tuple['EntityValue', 'EntityValue']]:

        active_triggers = {}
        for interp in interpretations:
            for ref in interp.core_state_assertions:
                types = self.get_types(ref)
                if 'trigger' in types:
                    active_triggers[ref.name] = interp.core_state_assertions[ref]
        result = {}
        for ref in self.active:
            if 'trigger' in ref.types and not active_triggers.get(ref.name):
                result[ref] = self.context[ref], false_value
        return result


    def execute_interpreters(self, interpreters: FrozenSet[RuleInterpreter], seed=1) -> context_diff:

        interpretations = {interpreter.interpret(self.context) for interpreter in interpreters}
        applicable = frozenset({x for x in interpretations if x.state == RuleInterpretationState.APPLICABLE})
        if not applicable:
            return dict()
        # trigger_nullifiers = get_trigger_nullifiers(self)
        conflicts = identify_conflicts(applicable)
        resolved = resolve_conflict_map(conflicts)
        invalidated_triggers = self.get_invalidated_triggers(resolved)
        resolved_changes = compress_interpretations(resolved)
        all_changes = resolved_changes | invalidated_triggers
        self.context, changes = self.context.update(all_changes)
        return changes

    def tick(self, count: int = 1) -> context_diff:
        output = dict()
        if count > 0:
            #  tick forward
            for tick in range(count):
                seed = randint(0, 1000)
                output |= self.execute_interpreters(frozenset(self.rule_interpreters), seed=seed)
            self.history = (output,) + self.history
        elif count < 0:
            # tick backward
            for tick in range(abs(count)):
                this_tick = self.history[0]
                self.history = self.history[1:]
                resolved = MPLEngine.invert_diff(this_tick)
                resolved_changes = compress_interpretations(resolved)
                self.context, output = self.context.update(resolved_changes)
        return output

    @staticmethod
    def invert_diff(diff: context_diff) -> FrozenSet[RuleInterpretation]:
        from mpl.interpreter.expression_evaluation.entity_value import EntityValue

        diff_change = dict()
        diff_descriptors = list()
        for key, diff_item in diff.items():
            diff_change[key] = diff_item[0]
            descriptor = f'{key}::{diff_item[1]}→{diff_item[0]}'
            diff_descriptors.append(descriptor)
        name = ';'.join(diff_descriptors)
        interpretation = RuleInterpretation(RuleInterpretationState.APPLICABLE, diff_change, name)
        return fs(interpretation)

    def activate(self, ref: Reference | Set[Reference],  value: Any = None) -> context_diff:
        self.context, changes = self.context.activate(ref, value)
        return changes

    def deactivate(self, ref: Reference | Set[Reference]) -> context_diff:
        self.context, changes = self.context.deactivate(ref)
        return changes

    def query(self, ref: Reference) -> 'EntityValue':
        value = self.context[ref]
        return value

    def get_types(self, ref: Reference) -> FrozenSet[str]:
        tmp = self.graph.out_edges(ref.without_types, data='relationship')
        result = {ref_type for ref, ref_type, edge in tmp if edge == Relationship.IS_A}
        return frozenset(result)

    @property
    def active(self) -> Dict[Reference, 'EntityValue']:
        return self.context.active

    def __hash__(self):
        context_hash = hash(self.context)
        edges = self.graph.edges(data='relationship')
        edges_as_set = frozenset(edges)
        return hash((context_hash, frozenset(self.rule_interpreters), edges_as_set, self.history))

    def __str__(self):
        return f'MPLEngine({self.context}, {self.rule_interpreters}, {self.history})'


def get_trigger_nullifiers(engine: MPLEngine) -> FrozenSet[RuleInterpretation]:
    from mpl.interpreter.expression_evaluation.interpreters.scenario_expression_interpreter import ScenarioResult
    from mpl.interpreter.expression_evaluation.entity_value import false_value
    from mpl.interpreter.expression_evaluation.entity_value import true_value
    result = set()
    for ref in engine.context.active:
        if 'trigger' in ref.types:
            sr = {ScenarioResult(false_value)}
            tmp = RuleInterpretation(
                RuleInterpretationState.APPLICABLE,
                {
                    ref: false_value,
                    ref.void: true_value
                },
                f'{ref}::%{{0}}→0',
                frozenset(sr),
                {
                    ref.void: 'TARGET',
                    ref: 'CONSUME'
                },
            )
            result.add(tmp)
    return frozenset(result)
