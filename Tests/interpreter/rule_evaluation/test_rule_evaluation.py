from dataclasses import dataclass

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.reference_resolution.mpl_entity import MPLEntity
from mpl.interpreter.rule_evaluation import RuleInterpretation, RuleInterpretationState, create_rule_interpreter
from mpl.lib.query_logic import MPL_Context
from mpl.lib import fs


@dataclass(frozen=True, order=True)
class RuleEvaluation:
    source: str
    context: MPL_Context


RE = RuleEvaluation


def test_evaluate_rule():


    contexts = {
        'simple': {
            Reference('a'): MPLEntity('a', fs(1)),
            Reference('b'): MPLEntity('b', fs()),
        },
        'simple with c and d': {
            Reference('a'): MPLEntity('a', fs(1)),
            Reference('b'): MPLEntity('b', fs()),
            Reference('c'): MPLEntity('c', fs(123)),
            Reference('d'): MPLEntity('d', fs()),
        },
        'recovery': {
            Reference('Recover'): MPLEntity('Recover', fs(5)),
            Reference('Hurt'): MPLEntity('Hurt', fs(1)),
            Reference('Ok'): MPLEntity('Ok', fs()),
        },
        'simpler wumpus': {
            Reference('Enter Strike Zone'): MPLEntity('Enter Strike Zone', fs(1)),
            Reference('Feel Secure'): MPLEntity('Feel Secure', fs(12)),
            Reference('Attack'): MPLEntity('Attack', fs()),
        },
        'fleeing wumpus': {
            Reference('Smell Prey'): MPLEntity('Smell Prey', fs()),
            Reference('Flee'): MPLEntity('Flee', fs(2)),
            Reference('noise'): MPLEntity('noise', fs()),
            Reference('Feel Secure'): MPLEntity('Feel Secure', fs()),
        }

    }
    for k in contexts:
        contexts[k] = tuple(contexts[k].items())

    expectations = {
        RE('<Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack', contexts['simpler wumpus']):
            RuleInterpretation(
                RuleInterpretationState.APPLICABLE,
                {
                    Reference('Feel Secure'): MPLEntity('Feel Secure', fs()),
                    Reference('Attack'): MPLEntity('Attack', fs(1, 9, 12)),
                },
                scenarios=fs(9),
                source='<Enter Strike Zone> ~> %{9} -> Feel Secure -> Attack'
            ),
        RE('!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure', contexts['fleeing wumpus']): RuleInterpretation(
            RuleInterpretationState.APPLICABLE,
            {
                Reference('noise'): MPLEntity('noise', fs('safe')),
                Reference('Feel Secure'): MPLEntity('Feel Secure', fs(1)),
            },
            source='!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure'
        ),
        RE('Recover ~> Hurt -> Ok', contexts['recovery']): RuleInterpretation(RuleInterpretationState.APPLICABLE,
            {
                Reference('Hurt'): MPLEntity('Hurt', fs()),
                Reference('Ok'): MPLEntity('Ok', fs(1)),
            },
            source='Recover ~> Hurt -> Ok'
        ),
        RE('a -> b', contexts['simple']): RuleInterpretation(RuleInterpretationState.APPLICABLE,
            {
                Reference('a'): MPLEntity('a', fs()),
                Reference('b'): MPLEntity('b', fs(1)),
            },
            source='a -> b'
        ),
        RE('b -> a', contexts['simple']): RuleInterpretation(RuleInterpretationState.NOT_APPLICABLE, {
            Reference('a'): MPLEntity('a', fs(1)),
            Reference('b'): MPLEntity('b', fs()),
        }, source='b -> a'),
        RE('a -> c -> b', contexts['simple with c and d']): RuleInterpretation(RuleInterpretationState.APPLICABLE, {
            Reference('a'): MPLEntity('a', fs()),
            Reference('b'): MPLEntity('b', fs(1, 123)),
            Reference('c'): MPLEntity('c', fs()),
        }, source='a -> c -> b'),
    }

    for input, expectation in expectations.items():
        rule_expression = quick_parse(RuleExpression, input.source)
        interpreter = create_rule_interpreter(rule_expression)
        context = dict(input.context)
        actual = interpreter.interpret(context)
        assert actual == expectation, input.source
