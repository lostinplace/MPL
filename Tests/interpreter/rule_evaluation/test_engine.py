import random

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.expression_evaluation.entity_value import ev_fv
from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine


def test_basic_operations():
    rules_text = """
    One -> Two
    Two -> Three -> Four
    Four -> Five
    Six -> Seven
    One -> Three -> Five
    """

    rules_items = rules_text.split('\n')
    expressions = {quick_parse(RuleExpression, item) for item in rules_items if item.strip()}

    engine = MPLEngine()
    engine = engine.add(expressions)

    actual = engine.tick()
    assert not actual
    diff = engine.activate(Ref('One'))
    expected_diff = {
        Ref('One'): (
            ev_fv(),
            ev_fv(1)
        ),
        Ref('One.*'): (
            ev_fv(1),
            ev_fv(),
        ),
    }
    assert diff == expected_diff

    actual = engine.query(Ref('One'))
    assert actual == ev_fv(1)

    trials = 100
    tolerance = 0.075
    hit_5 = 0
    hit_two = 0
    random.seed(0)
    for i in range(trials):
        diff = engine.activate(Ref('One'))
        diff = engine.activate(Ref('Three'))
        assert engine.query(Ref('One'))
        tick_diff = engine.tick()
        if engine.query(Ref('Two')):
            diff = engine.tick()
            assert engine.query(Ref('Four'))
            diff = engine.tick(7)
            assert engine.query(Ref('Five'))
            hit_two += 1
        if engine.query(Ref('Five')):
            diff = engine.tick(7)
            assert not diff
            hit_5 += 1

        final_diff = engine.deactivate(Ref('Five'))
        still_active = engine.active
        assert not still_active

    assert hit_5 == trials
    from sympy import Interval
    acceptable_hit_two_range = Interval(trials/2 * (1-tolerance), trials/2 * (1+tolerance))

    assert hit_two in acceptable_hit_two_range


def test_evaluate_rule_from_wumpus_file():
    engine = MPLEngine.from_file('Tests/test_files/simple_wumpus.mpl')
    # testing `Activity.Recover ~> Health.Hurt -> Health.Ok`

    tmp = engine.activate(Ref('Wumpus.Health.Hurt'))
    tmp = engine.activate(Ref('Wumpus.Activity.Recover'))

    assert engine.query(Ref('Wumpus.Health.Hurt'))
    assert engine.query(Ref('Wumpus.Activity.Recover'))
    tmp = engine.tick()
    assert not engine.query(Ref('Wumpus.Health.Hurt'))
    assert engine.query(Ref('Wumpus.Activity.Recover'))
    assert engine.query(Ref('Wumpus.Health.Ok'))