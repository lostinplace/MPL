import dataclasses
import itertools
from dataclasses import dataclass
from enum import auto, Enum
from itertools import zip_longest
from numbers import Number
from typing import Tuple, FrozenSet, Optional, List, Dict

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperator
from mpl.interpreter.expression_evaluation.engine_context import EngineContext
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.interpreter.expression_evaluation.interpreters.assignment_expression_interpreter import AssignmentResult
from mpl.interpreter.expression_evaluation.interpreters.create_expression_interpreter import \
    create_expression_interpreter
from mpl.interpreter.expression_evaluation.interpreters.expression_interpreter import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.interpreters.query_expression_interpreter import QueryResult
from mpl.interpreter.expression_evaluation.interpreters.scenario_expression_interpreter import ScenarioResult
from mpl.interpreter.expression_evaluation.interpreters.target_exprression_interpreter import TargetResult

entry_ledger_key = Reference('{}')
scenario_ledger_key = Reference('{scenario}')

empty_set = frozenset()


class RuleInterpretationState(Enum):
    APPLICABLE = auto()
    NOT_APPLICABLE = auto()
    UNDETERMINED = auto()


@dataclasses.dataclass(frozen=True, order=True)
class RuleInterpretation:
    state: RuleInterpretationState
    changes: Dict[Reference | str, Tuple[EntityValue, EntityValue]]
    source: str = ''
    scenarios: FrozenSet[ScenarioResult] = frozenset()

    @property
    def scenario_weight(self) -> int:
        total_weight = 0
        for scenario in self.scenarios:
            match scenario:
                case ScenarioResult(weight=x):
                    total_weight += x
                case Number() as x:
                    total_weight += x

        return total_weight or 1

    @property
    def keys(self) -> FrozenSet[Reference]:
        return frozenset(self.changes.keys())

    def __hash__(self):
        return hash((self.state, tuple(self.changes.items()), self.scenarios))

    def __repr__(self):
        tmp = [f'{k}:{v0}->{v1}' for k, (v0, v1) in sorted(self.changes.items(), key=lambda x: x[0])]
        changes_formatted = ', '.join(tmp)
        return f'Interpretation({self.source}, changes={changes_formatted})'


def compress_result_cache(result_cache: List[EntityValue]) -> EntityValue:
    result = EntityValue()
    for value in result_cache:
        result |= value
    return result.clean


def interpret(self, context: EngineContext, interpreters: Tuple[ExpressionInterpreter], expression: RuleExpression) \
        -> RuleInterpretation:
    """
    replacement rule interpreter
    :param self:
    :param context:
    :param interpreters:
    :param expression:
    :return:
    """
    from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperator
    this_name = str(expression)

    result_context = context
    operation_pairs = itertools.zip_longest(interpreters, self.operators)
    result_cache = []
    all_changes = {}

    scenarios = frozenset()
    for interpreter, operator in operation_pairs:
        result = interpreter.interpret(result_context)

        match result, operator:
            case QueryResult() as x, MPLOperator() if not x.value:
                return RuleInterpretation(RuleInterpretationState.NOT_APPLICABLE, {}, this_name)
            case QueryResult(), MPLOperator(_, 'CONSUME', __, _):
                result_context, changes = result_context.clear(result.value.references)
                all_changes |= changes
                result_cache.append(result.value)
            case QueryResult(), MPLOperator(_, 'OBSERVE', __, _):
                result_cache.append(EntityValue.from_value(True))
            case AssignmentResult() as x, None:
                result_context, changes = result_context.update(x.change)
                all_changes |= changes
            case AssignmentResult() as x, MPLOperator(_, 'OBSERVE', __, _):
                result_context, changes = result_context.update(x.change)
                all_changes |= changes
                result_cache.append(EntityValue.from_value(True))
            case AssignmentResult() as x, MPLOperator(_, 'CONSUME', __, _):
                result_context, changes = result_context.update(x.change)
                all_changes |= changes
                result_context, changes = result_context.clear(x.change.references)
                all_changes |= changes
                result_cache.append(x.value)
            case ScenarioResult() as x, MPLOperator(_, 'CONSUME', __, _):
                # TODO: this isn't right.  When a scenario is consumed, its selection probability should decrease
                #  to indicate the selection.  This means that scenario results need to track the clause they originated
                #  from, but that means a better reference graph.  I'll come back to it later
                scenarios |= x.value
                result_cache.append(x.value)
            case ScenarioResult() as x, MPLOperator(_, 'OBSERVE', __, _):
                scenarios |= x.value
                result_cache.append(EntityValue.from_value(True))
            case TargetResult() as x, None:
                target_refs = x.value.references
                target_value = compress_result_cache(result_cache)
                target_changes = {ref: target_value for ref in target_refs}
                result_context, changes = result_context.update(target_changes)
                all_changes |= changes

    return RuleInterpretation(RuleInterpretationState.APPLICABLE, all_changes, this_name, scenarios)


@dataclass(frozen=True, order=True)
class RuleInterpreter:
    expression_interpreters: Tuple[ExpressionInterpreter, ...]
    operators: Tuple[MPLOperator, ...]
    name: Optional[str] = None
    expression: Optional[RuleExpression] = None

    def interpret(self, context: EngineContext) -> RuleInterpretation:
        return interpret(self, context, self.expression_interpreters, self.expression)

    @property
    def references(self):
        tmp = set()
        for interpreter in self.expression_interpreters:
            tmp |= interpreter.references
        return frozenset(tmp)

    @staticmethod
    def from_expression(expression: RuleExpression) -> 'RuleInterpreter':
        return create_rule_interpreter(expression)


def create_rule_interpreter(rule: RuleExpression) -> RuleInterpreter:
    """
    Create a rule interpreter for a rule.
    :param rule: The rule to create an interpreter for.
    :return: The rule interpreter.
    """
    interpreters = []
    for clause, operator in zip_longest(rule.clauses, rule.operators):
        interpreter = None
        match clause, operator:
            case x, None:
                interpreter = create_expression_interpreter(x, True)
            case x, __:
                interpreter = create_expression_interpreter(x)
        interpreters.append(interpreter)

    return RuleInterpreter(tuple(interpreters), rule.operators, str(rule), rule)
