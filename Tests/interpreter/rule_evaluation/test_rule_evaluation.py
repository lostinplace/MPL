from dataclasses import dataclass

from sympy import symbols

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, Ref
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression

from mpl.interpreter.rule_evaluation import RuleInterpretation, RuleInterpretationState, create_rule_interpreter
from mpl.interpreter.expression_evaluation.entity_value import EntityValue, ev_fv, false_value, true_value
from mpl.lib import fs
from mpl.lib.context_tree.context_tree_implementation import ContextTree
from mpl.interpreter.expression_evaluation.engine_context import EngineContext


@dataclass(frozen=True, order=True)
class RuleEvaluation:
    source: str
    context: ContextTree

RE = RuleEvaluation


def quick_change(start, end):
    return ev_fv(start), ev_fv(end)


input_contexts = {
        'simple': {
            Reference('a'): ev_fv(1),
            Reference('b'): ev_fv(),
        },
        'simple with c and d': {
            Reference('a'): ev_fv(1),
            Reference('b'): ev_fv(),
            Reference('c'): ev_fv(123),
            Reference('d'): ev_fv(),
        },
        'recovery': {
            Reference('Recover'): ev_fv(5),
            Reference('Hurt'): ev_fv(True),
            Reference('Ok'): ev_fv(),
        },
        'simpler wumpus': {
            Reference('Enter Strike Zone'): ev_fv(1),
            Reference('Feel Secure'): ev_fv(12),
            Reference('Attack'): ev_fv(),
        },
        'fleeing wumpus': {
            Reference('Smell Prey'): ev_fv(),
            Reference('Flee'): ev_fv(2),
            Reference('noise'): ev_fv(),
            Reference('Feel Secure'): ev_fv(),
        }

    }


def test_evaluate_rule():
    contexts = {}

    for k, values in input_contexts.items():
        ctx = EngineContext.from_dict(values)
        contexts[k] = ctx

    expectations = {
        ('b.* -> d', contexts['simple with c and d']): RuleInterpretation(
            RuleInterpretationState.APPLICABLE,
            {
                Reference('b'): quick_change({}, True),
                Reference('b.*'): quick_change(True, {}),
                Reference('d'): quick_change({}, True),
                Reference('d.*'): quick_change(True, {}),
            },
            source='b.* -> d',
            core_state_assertions={
                Reference('b.*'): 'CONSUME',
                Reference('d'): 'TARGET',
            },
            scenarios=fs(1)
        ),
        ('Recover ~> Hurt -> Ok', contexts['recovery']): RuleInterpretation(
            RuleInterpretationState.APPLICABLE,
            {
                Reference('Hurt'): quick_change(True, {}),
                Reference('Hurt.*'): quick_change({}, True),
                Reference('Ok'): quick_change({}, True),
                Reference('Ok.*'): quick_change(True, {}),
            },
            source='Recover ~> Hurt -> Ok',
            scenarios=fs(1),
            core_state_assertions={
                Reference('Hurt'): 'CONSUME',
                Reference('Ok'): 'TARGET',
            }

        ),
        ('!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure', contexts['fleeing wumpus']): RuleInterpretation(
            RuleInterpretationState.APPLICABLE,
            {
                Reference('noise'): quick_change({}, symbols('`safe`')),
                Reference('noise.*'): quick_change(True, {}),
                Reference('Feel Secure'): quick_change({}, True),
                Reference('Feel Secure.*'): quick_change(True, {}),
            },
            source='!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure',
            scenarios=fs(1),
            core_state_assertions={
                Reference('noise'): 'TARGET',
                Reference('noise.*'): 'TARGET',
                Reference('Feel Secure'): 'TARGET',
            }
        ),
        ('<Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack', contexts['simpler wumpus']):
            RuleInterpretation(
                RuleInterpretationState.APPLICABLE,
                {
                    Reference('Feel Secure'): quick_change(12, {}),
                    Reference('Feel Secure.*'): quick_change({}, True),
                    Reference('Attack.*'): quick_change(True, {}),
                    Reference('Attack'): quick_change({}, {9, Ref('Feel Secure'), 12}),
                },
                source='<Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack',
                scenarios=ev_fv(9),
                core_state_assertions={
                    Reference('Feel Secure'): 'CONSUME',
                    Reference('Attack'): 'TARGET',
                }
            ),
        ('a -> b', contexts['simple']): RuleInterpretation(
            RuleInterpretationState.APPLICABLE,
            {
                Reference('a'): quick_change(1, 0),
                Reference('a.*'): quick_change(0, 1),
                Reference('b'): quick_change(0, 1),
                Reference('b.*'): quick_change(1, 0),
            },
            source='a -> b',
            scenarios=fs(1),
            core_state_assertions={
                Reference('a'): 'CONSUME',
                Reference('b'): 'TARGET',
            }
        ),
        ('b -> a', contexts['simple']): RuleInterpretation(RuleInterpretationState.NOT_APPLICABLE, {}, source='b -> a'),
        ('a -> c -> b', contexts['simple with c and d']): RuleInterpretation(
            RuleInterpretationState.APPLICABLE,
            {
                Reference('a'): quick_change(1, 0),
                Reference('a.*'): quick_change(0, True),
                Reference('b'): quick_change(0, {1, 123, Ref('a'), Ref('b')}),
                Reference('b.*'): quick_change(True, 0),
                Reference('c'): quick_change(123, 0),
                Reference('c.*'): quick_change(0, True),
            },
            source='a -> c -> b',
            scenarios=fs(1),
            core_state_assertions={
                Reference('a'): 'CONSUME',
                Reference('c'): 'CONSUME',
                Reference('b'): 'TARGET',
            }
        ),
    }

    for (rule, context), expected in expectations.items():
        rule_expression = quick_parse(RuleExpression, rule)
        interpreter = create_rule_interpreter(rule_expression)
        actual = interpreter.interpret(context)
        assert actual == expected, rule

