from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpressionParsers, AssignmentExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression
from Parser.ExpressionParsers.rule_expression_parser import Rule, RuleExpressionParsers, RuleClause
from Parser.ExpressionParsers.state_expression_parser import StateExpression
from Parser.Tokenizers.operator_tokenizers import MPLOperator
from Tests import qre, collect_parsing_expectations, qse, quick_parse


def test_rule_expression_parsers():
    expectations = {
        'Exit Strike Zone *~> Near Prey -> $': Rule(
            [
                RuleClause('trigger', qse('Exit Strike Zone')),
                RuleClause('state', qse('Near Prey')),
                RuleClause('state', qse('$')),
            ],
            [
                MPLOperator('TRIGGER', 'OBSERVE', 'STATE', 17),
                MPLOperator('ANY', 'CONSUME', 'STATE', 31),
            ],
        ),
        'Ok ~? Turns Wounded > 0 ~@ Turns Wounded -= 1': Rule(
            [
                RuleClause('state', qse('Ok')),
                RuleClause('query', quick_parse(LogicalExpression, 'Turns Wounded > 0')),
                RuleClause('action', quick_parse(AssignmentExpression, 'Turns Wounded -= 1')),
            ],
            [MPLOperator('ANY', 'OBSERVE', 'QUERY', 3), MPLOperator('ANY', 'OBSERVE', 'ACTION', 24)]
        ),
        'Hurt: Health ~> Feel Secure -% 10 -> Feel Secure': Rule(
            [
                RuleClause('state', quick_parse(StateExpression, 'Hurt: Health')),
                RuleClause('state', quick_parse(StateExpression, 'Feel Secure')),
                RuleClause('scenario', quick_parse(ArithmeticExpression, '10')),
                RuleClause('state', quick_parse(StateExpression, 'Feel Secure')),
            ],
            [
                MPLOperator('ANY', 'OBSERVE', 'STATE', 13),
                MPLOperator('ANY', 'CONSUME', 'SCENARIO', 28),
                MPLOperator('ANY', 'CONSUME', 'STATE', 34),
            ]
        ),
        'Stab *~> Ok -> Hurt': Rule(
            [
                RuleClause('trigger', qse('Stab')),
                RuleClause('state', qse('Ok')),
                RuleClause('state', qse('Hurt')),
            ],
            [MPLOperator('TRIGGER', 'OBSERVE', 'STATE', 5), MPLOperator('ANY', 'CONSUME', 'STATE', 12)],
        ),
        'Hurt ~@ Turns Wounded: INT += 1': Rule(
            [
                RuleClause(
                    'state',
                    qse('Hurt')
                ),
                RuleClause(
                    'action',
                    AssignmentExpressionParsers.expression.parse('Turns Wounded: INT += 1').value
                )
            ],
            [MPLOperator('ANY', 'OBSERVE', 'ACTION', 5)],
        ),
        "a *-> b": Rule(
            [
                RuleClause(
                    'trigger',
                    StateExpression([qre('a')], []),
                ),
                RuleClause(
                    'state',
                    StateExpression([qre('b')], []),
                ),
            ],
            [
                MPLOperator('TRIGGER', 'CONSUME', 'STATE', 2)
            ]
        ),

    }

    for result in collect_parsing_expectations(expectations, RuleExpressionParsers.expression):
        result = result.as_strings()
        assert result.actual == result.expected
