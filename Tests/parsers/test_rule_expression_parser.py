from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression, RuleExpressionParsers, RuleClause
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression
from mpl.Parser.ExpressionParsers.state_expression_parser import StateExpression
from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperator
from Tests import collect_parsing_expectations, qse, quick_parse


expectations = {
        '!Smell Prey & Flee ~@ noise = `safe` ~> Feel Secure': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, '!Smell Prey & Flee')),
                RuleClause('action', quick_parse(AssignmentExpression, 'noise = `safe`')),
                RuleClause('query', quick_parse(QueryExpression, 'Feel Secure')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'ACTION', 19), MPLOperator('ANY', 'OBSERVE', 'STATE', 37))
        ),
        'Smell Prey & !Feel Secure ~> Wander -> Flee': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, 'Smell Prey & !Feel Secure')),
                RuleClause('query', quick_parse(QueryExpression, 'Wander')),
                RuleClause('query', quick_parse(QueryExpression, 'Flee')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'STATE', 26), MPLOperator('ANY', 'CONSUME', 'STATE', 36))
        ),
        ' * & Ok ~> Feel Secure': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, '* & Ok')),
                RuleClause('query', quick_parse(QueryExpression, 'Feel Secure')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'STATE', 8),)
        ),
        'Hurt ~@ Turns Wounded: int += 1': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, 'Hurt')),
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
                RuleClause('query', quick_parse(QueryExpression, 'Feel Secure')),
            ),
            (MPLOperator('ANY', 'CONSUME', 'STATE', 6),)
        ),
        'Distance To Prey > Smell Range -> Smell Prey -> *': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, 'Distance To Prey > Smell Range')),
                RuleClause('query', quick_parse(QueryExpression, 'Smell Prey')),
                RuleClause('query', quick_parse(QueryExpression, '*')),
            ),
            (
                MPLOperator('ANY', 'CONSUME', 'STATE', 31),
                MPLOperator('ANY', 'CONSUME', 'STATE', 45),
            )
        ),
        '<Exit Strike Zone> ~> Near Prey -> <Free>': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, '<Exit Strike Zone>')),
                RuleClause('query', quick_parse(QueryExpression, 'Near Prey')),
                RuleClause('query', quick_parse(QueryExpression, '<Free>')),
            ),
            (
                MPLOperator('ANY', 'OBSERVE', 'STATE', 19),
                MPLOperator('ANY', 'CONSUME', 'STATE', 32),
            ),
        ),
        'Ok ~> Turns Wounded > 0 ~@ Turns Wounded -= 1': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, 'Ok')),
                RuleClause('query', quick_parse(QueryExpression, 'Turns Wounded > 0')),
                RuleClause('action', quick_parse(AssignmentExpression, 'Turns Wounded -= 1')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'STATE', 3), MPLOperator('ANY', 'OBSERVE', 'ACTION', 24))
        ),
        'Hurt: Health ~> Feel Secure -> %{10} -> Feel Secure': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, 'Hurt: Health')),
                RuleClause('query', quick_parse(QueryExpression, 'Feel Secure')),
                RuleClause('scenario', quick_parse(ScenarioExpression, '%{10}')),
                RuleClause('query', quick_parse(QueryExpression, 'Feel Secure')),
            ),
            (
                MPLOperator('ANY', 'OBSERVE', 'STATE', 13),
                MPLOperator('ANY', 'CONSUME', 'STATE', 28),
                MPLOperator('ANY', 'CONSUME', 'STATE', 37),
            )
        ),
        '<Stab> ~> Ok -> Hurt': RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, '<Stab>')),
                RuleClause('query', quick_parse(QueryExpression, 'Ok')),
                RuleClause('query', quick_parse(QueryExpression, 'Hurt')),
            ),
            (MPLOperator('ANY', 'OBSERVE', 'STATE', 7), MPLOperator('ANY', 'CONSUME', 'STATE', 13)),
        ),
        "a -> <b>": RuleExpression(
            (
                RuleClause('query', quick_parse(QueryExpression, 'a')),
                RuleClause('query', quick_parse(QueryExpression, '<b>')),
            ),
            (MPLOperator('ANY', 'CONSUME', 'STATE', 2),)
        ),

    }


def test_rule_expression_parsers():

    for result in collect_parsing_expectations(expectations, RuleExpressionParsers.expression):
        result = result.as_strings()
        assert result.actual.replace('Tracked', '') == result.expected.replace('Tracked', '') , result.parser_input


def test_rule_expression_string_converstion():

    for expectation in expectations:
        result = quick_parse(RuleExpression, expectation)
        actual = str(result)
        assert actual.strip() == expectation.strip()