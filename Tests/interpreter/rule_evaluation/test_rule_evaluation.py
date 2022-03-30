from dataclasses import dataclass

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression

from mpl.interpreter.rule_evaluation import RuleInterpretation, RuleInterpretationState, create_rule_interpreter
from mpl.interpreter.expression_evaluation.entity_value import EntityValue
from mpl.lib import fs
from mpl.lib.context_tree.context_tree_implementation import ContextTree


@dataclass(frozen=True, order=True)
class RuleEvaluation:
    source: str
    context: ContextTree


RE = RuleEvaluation


def test_evaluate_rule():


    contexts = {
        'simple': {
            Reference('a'): EntityValue(fs(1)),
            Reference('b'): EntityValue(fs()),
        },
        'simple with c and d': {
            Reference('a'): EntityValue(fs(1)),
            Reference('b'): EntityValue(fs()),
            Reference('c'): EntityValue(fs(123)),
            Reference('d'): EntityValue(fs()),
        },
        'recovery': {
            Reference('Recover'): EntityValue(fs(5)),
            Reference('Hurt'): EntityValue(fs(1)),
            Reference('Ok'): EntityValue(fs()),
        },
        'simpler wumpus': {
            Reference('Enter Strike Zone'): EntityValue(fs(1)),
            Reference('Feel Secure'): EntityValue(fs(12)),
            Reference('Attack'): EntityValue(fs()),
        },
        'fleeing wumpus': {
            Reference('Smell Prey'): EntityValue(fs()),
            Reference('Flee'): EntityValue(fs(2)),
            Reference('noise'): EntityValue(fs()),
            Reference('Feel Secure'): EntityValue(fs()),
        }

    }
    for k in contexts:
        contexts[k] = tuple(contexts[k].items())

    expectations = {
        RE('<Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack', contexts['simpler wumpus']):
            RuleInterpretation(
                RuleInterpretationState.APPLICABLE,
                {
                    Reference('Feel Secure'): EntityValue(fs()),
                    Reference('Attack'): EntityValue(fs(1, 9, 12)),
                },
                scenarios=fs(9),
                source='<Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack'
            ),
        RE('!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure', contexts['fleeing wumpus']): RuleInterpretation(
            RuleInterpretationState.APPLICABLE,
            {
                Reference('noise'): EntityValue(fs('safe')),
                Reference('Feel Secure'): EntityValue(fs(1)),
            },
            source='!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure'
        ),
        RE('Recover ~> Hurt -> Ok', contexts['recovery']): RuleInterpretation(RuleInterpretationState.APPLICABLE,
            {
                Reference('Hurt'): EntityValue(fs()),
                Reference('Ok'): EntityValue(fs(1)),
            },
            source='Recover ~> Hurt -> Ok'
        ),
        RE('a -> b', contexts['simple']): RuleInterpretation(RuleInterpretationState.APPLICABLE,
            {
                Reference('a'): EntityValue(fs()),
                Reference('b'): EntityValue(fs(1)),
            },
            source='a -> b'
        ),
        RE('b -> a', contexts['simple']): RuleInterpretation(RuleInterpretationState.NOT_APPLICABLE, {
            Reference('a'): EntityValue(fs(1)),
            Reference('b'): EntityValue(fs()),
        }, source='b -> a'),
        RE('a -> c -> b', contexts['simple with c and d']): RuleInterpretation(RuleInterpretationState.APPLICABLE, {
            Reference('a'): EntityValue(fs()),
            Reference('b'): EntityValue(fs(1, 123)),
            Reference('c'): EntityValue(fs()),
        }, source='a -> c -> b'),
    }

    for input, expectation in expectations.items():
        rule_expression = quick_parse(RuleExpression, input.source)
        interpreter = create_rule_interpreter(rule_expression)
        context = dict(input.context)
        actual = interpreter.interpret(context)
        assert actual == expectation, input.source
