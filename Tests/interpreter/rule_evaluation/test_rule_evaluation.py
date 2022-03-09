from dataclasses import dataclass

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntity, MPLEntityClass
from mpl.interpreter.rule_evaluation import RuleInterpretation, RuleInterpretationState, create_rule_interpreter
from mpl.lib import fs
from mpl.lib.query_logic import MPL_Context


@dataclass(frozen=True, order=True)
class RuleEvaluation:
    source: str
    context: MPL_Context


RE = RuleEvaluation


def test_evaluate_rule():
    contexts = {
        'simple': {
            Reference('a'): MPLEntity(0, 'a', MPLEntityClass.STATE, fs(1)),
            Reference('b'): MPLEntity(1, 'b', MPLEntityClass.STATE, fs()),
        },
        'simple with c and d': {
            Reference('a'): MPLEntity(0, 'a', MPLEntityClass.STATE, fs(1)),
            Reference('b'): MPLEntity(1, 'b', MPLEntityClass.STATE, fs()),
            Reference('c'): MPLEntity(1, 'c', MPLEntityClass.STATE, fs(123)),
            Reference('d'): MPLEntity(1, 'd', MPLEntityClass.STATE, fs()),
        },
        'recovery': {
            Reference('Recover'): MPLEntity(0, 'Recover', MPLEntityClass.STATE, fs(5)),
            Reference('Hurt'): MPLEntity(1, 'Hurt', MPLEntityClass.STATE, fs(1)),
            Reference('Ok'): MPLEntity(1, 'Ok', MPLEntityClass.STATE, fs()),
        },
        'simpler wumpus': {
            Reference('Enter Strike Zone'): MPLEntity(0, 'Enter Strike Zone', MPLEntityClass.TRIGGER, fs(1)),
            Reference('Feel Secure'): MPLEntity(1, 'Feel Secure', MPLEntityClass.STATE, fs(12)),
            Reference('Attack'): MPLEntity(1, 'Attack', MPLEntityClass.STATE, fs()),
        },
        'fleeing wumpus': {
            Reference('Smell Prey'): MPLEntity(1, 'Smell Prey', MPLEntityClass.STATE, fs()),
            Reference('Flee'): MPLEntity(1, 'Flee', MPLEntityClass.STATE, fs(2)),
            Reference('noise'): MPLEntity(1, 'noise', MPLEntityClass.STATE, fs()),
            Reference('Feel Secure'): MPLEntity(1, 'Feel Secure', MPLEntityClass.STATE, fs()),
        }

    }
    for k in contexts:
        contexts[k] = tuple(contexts[k].items())

    expectations = {
        RE('<Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack', contexts['simpler wumpus']):
            RuleInterpretation(
                RuleInterpretationState.APPLICABLE,
                {
                    Reference('Feel Secure'): MPLEntity(1, 'Feel Secure', MPLEntityClass.STATE, fs()),
                    Reference('Attack'): MPLEntity(1, 'Attack', MPLEntityClass.STATE, fs(1, 9, 12)),
                },
                scenarios=fs(9),
                source='<Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack'
            ),
        RE('!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure', contexts['fleeing wumpus']): RuleInterpretation(
            RuleInterpretationState.APPLICABLE,
            {
                Reference('noise'): MPLEntity(1, 'noise', MPLEntityClass.STATE, fs('safe')),
                Reference('Feel Secure'): MPLEntity(1, 'Feel Secure', MPLEntityClass.STATE, fs(1)),
            },
            source='!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure'
        ),
        RE('Recover ~> Hurt -> Ok', contexts['recovery']): RuleInterpretation(RuleInterpretationState.APPLICABLE,
            {
                Reference('Hurt'): MPLEntity(1, 'Hurt', MPLEntityClass.STATE, fs()),
                Reference('Ok'): MPLEntity(1, 'Ok', MPLEntityClass.STATE, fs(1)),
            },
            source='Recover ~> Hurt -> Ok'
        ),
        RE('a -> b', contexts['simple']): RuleInterpretation(RuleInterpretationState.APPLICABLE,
            {
                Reference('a'): MPLEntity(0, 'a', MPLEntityClass.STATE, fs()),
                Reference('b'): MPLEntity(1, 'b', MPLEntityClass.STATE, fs(1)),
            },
            source='a -> b'
        ),
        RE('b -> a', contexts['simple']): RuleInterpretation(RuleInterpretationState.NOT_APPLICABLE, {
            Reference('a'): MPLEntity(0, 'a', MPLEntityClass.STATE, fs(1)),
            Reference('b'): MPLEntity(1, 'b', MPLEntityClass.STATE, fs()),
        }, source='b -> a'),
        RE('a -> c -> b', contexts['simple with c and d']): RuleInterpretation(RuleInterpretationState.APPLICABLE, {
            Reference('a'): MPLEntity(0, 'a', MPLEntityClass.STATE, fs()),
            Reference('b'): MPLEntity(1, 'b', MPLEntityClass.STATE, fs(1, 123)),
            Reference('c'): MPLEntity(1, 'c', MPLEntityClass.STATE, fs()),
        }, source='a -> c -> b'),
    }

    for input, expectation in expectations.items():
        rule_expression = quick_parse(RuleExpression, input.source)
        interpreter = create_rule_interpreter(rule_expression)
        context = dict(input.context)
        actual = interpreter.interpret(context)
        assert actual == expectation, input.source
