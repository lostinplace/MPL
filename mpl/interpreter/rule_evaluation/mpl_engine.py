from dataclasses import dataclass
from typing import Set, Dict, Tuple, Any, Iterable, FrozenSet, List, Generator

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.conflict_resolution import identify_conflicts, resolve_conflicts
from mpl.interpreter.expression_evaluation.engine_context import EngineContext, context_diff
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity
from mpl.interpreter.rule_evaluation import RuleInterpreter, RuleInterpretationState, RuleInterpretation
from mpl.lib import fs


@dataclass(order=True)
class MPLEngine:
    rule_interpreters: Set[RuleInterpreter] = frozenset()
    context: EngineContext = EngineContext()
    history: Tuple[context_diff, ...] = ()

    def add(self, rules: RuleExpression | Set[RuleExpression]):
        rule: Set[RuleExpression]
        if not isinstance(rules, Iterable):
            rules = {rules}
        for rule in rules:
            interpreter = RuleInterpreter.from_expression(rule)
            tmp_context = EngineContext.from_interpreter(interpreter)
            new_context = tmp_context | self.context
            self.rule_interpreters |= fs(interpreter)
            self.context = new_context

    def apply(self, interpretations: FrozenSet[RuleInterpretation]):
        original_context = self.context
        new_context = self.context.apply(interpretations)
        self.context = new_context
        return original_context.get_diff(self.context)

    def tick(self, count: int = 1) -> Dict[str, Tuple[Any, Any]]:
        original_context = self.context
        if count > 0:
            #  tick forward
            for tick in range(count):
                interpretations = set()
                for rule_interpreter in self.rule_interpreters:
                    result = rule_interpreter.interpret(self.context)
                    if result.state == RuleInterpretationState.APPLICABLE:
                        interpretations.add(result)
                conflicts = identify_conflicts(interpretations)
                resolved = resolve_conflicts(conflicts)
                self.apply(resolved)

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
        diff_change = dict()
        diff_descriptors = list()
        for key, diff_item in diff.items():
            key = Reference(key)
            diff_change[key] = MPLEntity.from_reference(key, diff_item[0])
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
        value = self.context.get(ref)
        match value:
            case MPLEntity():
                return value.value
            case _:
                return value

    @property
    def active(self) -> FrozenSet[Reference]:
        return self.context.active

    def evaluate_rule(self, rule):
        return self.mpl_interpreter.evaluate_rule(rule)