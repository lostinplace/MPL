import random

from Tests import quick_parse
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine
from mpl.lib import fs


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
    engine.add(expressions)

    actual = engine.tick()
    assert not actual
    diff = engine.activate(Ref('One'))
    assert diff == {
        'One': (
            fs(),
            fs(Ref('One').id
        ))
    }
    actual = engine.query(Ref('One'))
    assert actual == fs(Ref('One').id)

    trials = 1000
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
    min = trials / 2 * 0.95
    max = trials / 2 * 1.05
    assert hit_two > min and hit_two < max


def test_evaluate_rule_from_wumpus_file():
    engine = MPLEngine.from_file('Tests/test_files/simple_wumpus.mpl')
    testing = """Activity.Recover ~> Health.Hurt -> Health.Ok"""
    tmp = engine.query(Ref('Wumpus.Health.Ok'))
    assert not tmp
    tmp = engine.activate(Ref('Wumpus.Health.Hurt'))
    tmp = engine.activate(Ref('Wumpus.Activity.Recover'))
    assert tmp
    assert engine.query(Ref('Wumpus.Health.Hurt'))
    assert engine.query(Ref('Wumpus.Activity.Recover'))
    tmp = engine.tick()
    assert not engine.query(Ref('Wumpus.Health.Hurt'))
    assert engine.query(Ref('Wumpus.Activity.Recover'))
    assert engine.query(Ref('Wumpus.Health.Ok'))