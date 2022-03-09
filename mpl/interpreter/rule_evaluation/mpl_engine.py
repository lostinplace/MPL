from dataclasses import dataclass
from typing import Set, Dict, Tuple, Any, Iterable, FrozenSet

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
        return output

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