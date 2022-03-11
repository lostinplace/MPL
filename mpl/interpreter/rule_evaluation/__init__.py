import dataclasses
from dataclasses import dataclass
from enum import auto, Enum
from functools import reduce
from itertools import zip_longest
from numbers import Number
from typing import Tuple, FrozenSet, Optional

from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleClause
from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperator
from mpl.interpreter.expression_evaluation.interpreters import ExpressionInterpreter
from mpl.interpreter.expression_evaluation.interpreters import AssignmentResult, create_expression_interpreter, \
    QueryResult, ScenarioResult, TargetResult
from mpl.interpreter.expression_evaluation.types import QueryLedgerRef, ChangeLedgerRef
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntityClass, MPLEntity
from mpl.lib import fs
from mpl.lib.query_logic import MPL_Context, FinalResultSet

entry_ledger_key = Reference('{}')
scenario_ledger_key = Reference('{scenario}')

empty_set = frozenset()


def clear_entity_values(context: MPL_Context, values: FinalResultSet) -> MPL_Context:
    entities = [x for x in values if isinstance(x, MPLEntity) and x.entity_class & MPLEntityClass.CLEARED_BY_CONSUMPTION]
    new_vals = dict()
    change_ledger = context.get(ChangeLedgerRef) or dict()
    for k, v in context.items():
        if v in entities:
            new_value = dataclasses.replace(v, value=frozenset())
            new_vals[k] = new_value
            change_ledger[k] = new_value
        else:
            new_vals[k] = v
    update = {ChangeLedgerRef: change_ledger}
    return new_vals | update


def condense_values(values: FinalResultSet) -> FinalResultSet:
    out_vals = frozenset()
    for value in values:
        match value:
            case MPLEntity():
                out_vals |= value.value
            case _:
                out_vals |= {value}
    return out_vals


def compress_ledger(ledger:  Tuple[FinalResultSet, ...]) -> FinalResultSet:
    """
    Compress a ledger.
    :param ledger: The ledger to compress.
    :return: The compressed ledger.
    """
    return reduce(lambda x, y: x | y, ledger, frozenset())


def get_entities(source: FinalResultSet) -> FinalResultSet:
    return frozenset(x for x in source if isinstance(x, MPLEntity))


def assign_entity_values(context: MPL_Context, targets: FrozenSet[MPLEntity], values: FinalResultSet) -> MPL_Context:
    out_vals = condense_values(values)
    new_vals = dict()
    change_ledger = context.get(ChangeLedgerRef) or dict()
    for k, v in context.items():
        match k, v:
            case x, _ if x in {ChangeLedgerRef, QueryLedgerRef}:
                new_vals[k] = v
            case _, x if x not in targets:
                new_vals[k] = v
            case _, _:
                new_value = out_vals | v.value
                new_ent_value = dataclasses.replace(v, value=new_value)
                new_vals[k] = new_ent_value
                change_ledger[k] = new_ent_value
    update = {ChangeLedgerRef: change_ledger}
    return new_vals | update


class RuleInterpretationState(Enum):
    APPLICABLE = auto()
    NOT_APPLICABLE = auto()
    UNDETERMINED = auto()


@dataclass(frozen=True, order=True)
class RuleInterpretation:
    state: RuleInterpretationState
    changes: MPL_Context
    source: str = ''
    scenarios: FrozenSet[ScenarioResult] = frozenset()

    @property
    def scenario_weight(self) -> int:
        total_weight = 0
        for scenario in self.scenarios:
            match scenario:
                case ScenarioResult(weight=x):
                    total_weight += x
                case Number(x):
                    total_weight += x

        return total_weight or 1

    def __hash__(self):
        return hash((self.state, tuple(self.changes.items()), self.scenarios))

    def __repr__(self):
        return f'Interpretation({self.source})'


@dataclass(frozen=True, order=True)
class RuleInterpreter:
    expression_interpreters: Tuple[ExpressionInterpreter, ...]
    operators: Tuple[MPLOperator, ...]
    name: Optional[str] = None
    expression: Optional[RuleExpression] = None

    def interpret(self, context: MPL_Context) -> RuleInterpretation:
        this_name = self.name or ''
        result_context = context | {QueryLedgerRef: tuple()}
        operation_pairs = zip_longest(self.expression_interpreters, self.operators)
        scenarios = frozenset()
        for interpreter, operator in operation_pairs:
            result = interpreter.interpret(result_context)

            match result, operator:
                case QueryResult() as x, MPLOperator() if not x.value:
                    return RuleInterpretation(RuleInterpretationState.NOT_APPLICABLE, context, this_name)
                case QueryResult(), MPLOperator(_, 'CONSUME', __, _):
                    result_context = clear_entity_values(result_context, result.value)
                    value_condensed = condense_values(result.value)
                    result_context[QueryLedgerRef] = (value_condensed,) + result_context[QueryLedgerRef]
                case QueryResult(), MPLOperator(_, 'OBSERVE', __, _):
                    result_context[QueryLedgerRef] = (fs(1),) + result_context[QueryLedgerRef]
                case AssignmentResult() as x, None:
                    result_context |= x.value
                case AssignmentResult() as x, MPLOperator(_, 'OBSERVE', __, _):
                    result_context |= x.value
                    result_context[QueryLedgerRef] = (fs(1),) + result_context[QueryLedgerRef]
                case AssignmentResult() as x, MPLOperator(_, 'CONSUME', __, _):
                    result_context |= x.value
                    value_condensed = condense_values(result.value)
                    result_context[QueryLedgerRef] = (value_condensed,) + result_context[QueryLedgerRef]
                case ScenarioResult() as x, MPLOperator(_, 'CONSUME', __, _):
                    # TODO: this isn't right.  When a scenario is consumed, its selection probability should decrease
                    #  by ... some amount.  This means that scenario results need to track the clause they originated
                    #  from, but that means a better reference graph.  I'll come back to it later
                    scenarios |= x.value
                    value_condensed = condense_values(result.value)
                    result_context[QueryLedgerRef] = (value_condensed,) + result_context[QueryLedgerRef]
                case ScenarioResult() as x, MPLOperator(_, 'OBSERVE', __, _):
                    scenarios |= x.value
                    result_context[QueryLedgerRef] = (fs(1),) + result_context[QueryLedgerRef]
                case TargetResult(), None:
                    compressed_ledger = compress_ledger(result_context[QueryLedgerRef])
                    targets = get_entities(result.value)
                    result_context = assign_entity_values(result_context, targets, compressed_ledger)

        changes = result_context.get(ChangeLedgerRef) or dict()

        if QueryLedgerRef in result_context:
            del result_context[QueryLedgerRef]
        if ChangeLedgerRef in result_context:
            del result_context[ChangeLedgerRef]

        return RuleInterpretation(RuleInterpretationState.APPLICABLE, changes, this_name, scenarios)

    @property
    def references(self):
        tmp = set()
        for interpreter in self.expression_interpreters:
            tmp |= interpreter.references
        return frozenset(tmp)

    @staticmethod
    def from_expression(expression: RuleExpression) -> 'RuleInterpreter':
        return create_rule_interpreter(expression)


def rule_clause_to_expression_interpreter(clause: RuleClause, target=False) -> ExpressionInterpreter:
    return create_expression_interpreter(clause.expression, target)


def create_rule_interpreter(rule: RuleExpression) -> RuleInterpreter:
    """
    Create a rule interpreter for a rule.
    :param rule: The rule to create an interpreter for.
    :return: The rule interpreter.
    """
    interpreters = []
    for clause, operator in zip_longest(rule.clauses, rule.operators):
        match clause, operator:
            case x, None:
                interpreter = rule_clause_to_expression_interpreter(x, True)
            case x, __:
                interpreter = rule_clause_to_expression_interpreter(x)
        interpreters.append(interpreter)

    return RuleInterpreter(tuple(interpreters), rule.operators, str(rule), rule)

