from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression
from Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleExpressionParsers, RuleClause
from Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from Parser.ExpressionParsers.state_expression_parser import StateExpression
from Parser.Tokenizers.operator_tokenizers import MPLOperator
from Tests import qre, collect_parsing_expectations, qse, quick_parse
from lib.custom_parsers import debug


def test_rule_expression_parsers():
    expectations = {
        'Smell Prey & !Feel Secure ~> Wander -> Flee': RuleExpression(
            (
                RuleClause('state', quick_parse(StateExpression, 'Smell Prey & !Feel Secure')),
                RuleClause('state', quick_parse(StateExpression, 'Wander')),
                RuleClause('state', quick_parse(StateExpression, 'Flee')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'STATE', 26), MPLOperator('ANY', 'CONSUME', 'STATE', 36))
        ),
        ' * & Ok ~> Feel Secure': RuleExpression(
            (
                RuleClause('state', quick_parse(StateExpression, '* & Ok')),
                RuleClause('state', quick_parse(StateExpression, 'Feel Secure')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'STATE', 8),)
        ),
        'Hurt ~@ Turns Wounded: int += 1': RuleExpression(
            (
                RuleClause('state', qse('Hurt')),
                RuleClause(
                    'action',
                    quick_parse(AssignmentExpression, 'Turns Wounded: int += 1')
                )
            ),
            (MPLOperator('ANY', 'OBSERVE', 'ACTION', 5),),
        ),
        '%{10} -> Feel Secure': RuleExpression(
            (
                RuleClause('scenario', quick_parse(ScenarioExpression, '%{10}')),
                RuleClause('state', quick_parse(StateExpression, 'Feel Secure')),
            ),
            (MPLOperator('ANY', 'CONSUME', 'STATE', 6),)
        ),
        'Distance To Prey > Smell Range -> Smell Prey -> *': RuleExpression(
            (
                RuleClause('query', quick_parse(LogicalExpression, 'Distance To Prey > Smell Range')),
                RuleClause('state', qse('Smell Prey')),
                RuleClause('state', qse('*')),
            ),
            (
                MPLOperator('ANY', 'CONSUME', 'STATE', 31),
                MPLOperator('ANY', 'CONSUME', 'STATE', 45),
            )
        ),
        '<Exit Strike Zone> ~> Near Prey -> <Free>': RuleExpression(
            (
                RuleClause('state', qse('<Exit Strike Zone>')),
                RuleClause('state', qse('Near Prey')),
                RuleClause('state', qse('<Free>')),
            ),
            (
                MPLOperator('ANY', 'OBSERVE', 'STATE', 19),
                MPLOperator('ANY', 'CONSUME', 'STATE', 32),
            ),
        ),
        'Ok ~> Turns Wounded > 0 ~@ Turns Wounded -= 1': RuleExpression(
            (
                RuleClause('state', qse('Ok')),
                RuleClause('query', quick_parse(LogicalExpression, 'Turns Wounded > 0')),
                RuleClause('action', quick_parse(AssignmentExpression, 'Turns Wounded -= 1')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'STATE', 3), MPLOperator('ANY', 'OBSERVE', 'ACTION', 24))
        ),
        'Hurt: Health ~> Feel Secure -> %{10} -> Feel Secure': RuleExpression(
            (
                RuleClause('state', quick_parse(StateExpression, 'Hurt: Health')),
                RuleClause('state', quick_parse(StateExpression, 'Feel Secure')),
                RuleClause('scenario', quick_parse(ScenarioExpression, '%{10}')),
                RuleClause('state', quick_parse(StateExpression, 'Feel Secure')),
            ),
            (
                MPLOperator('ANY', 'OBSERVE', 'STATE', 13),
                MPLOperator('ANY', 'CONSUME', 'STATE', 28),
                MPLOperator('ANY', 'CONSUME', 'STATE', 37),
            )
        ),
        '<Stab> ~> Ok -> Hurt': RuleExpression(
            (
                RuleClause('state', qse('<Stab>')),
                RuleClause('state', qse('Ok')),
                RuleClause('state', qse('Hurt')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'STATE', 7), MPLOperator('ANY', 'CONSUME', 'STATE', 13)),
        ),
        "a -> <b>": RuleExpression(
            (
                RuleClause('state', qse('a')),
                RuleClause('state', quick_parse(StateExpression, '<b>')),
            ),
            (MPLOperator('ANY', 'CONSUME', 'STATE', 2),)
        ),

    }

    for result in collect_parsing_expectations(expectations, RuleExpressionParsers.expression ):
        result = result.as_strings()
        assert result.actual == result.expected
