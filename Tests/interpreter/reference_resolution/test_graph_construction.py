from Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from Parser.ExpressionParsers.logical_expression_parser import LogicalExpression
from Parser.ExpressionParsers.machine_expression_parser import parse_machine_file
from Parser.ExpressionParsers.reference_expression_parser import Reference, DeclarationExpression
from Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression

from Parser.ExpressionParsers.state_expression_parser import StateExpression
from Parser.Tokenizers.operator_tokenizers import MPLOperator
from Tests import quick_parse

from lib.simple_graph import SimpleGraph
from interpreter.reference_resolution.reference_graph_resolution import MPLLine, MPLEntity, get_entity_id, \
    declaration_expression_to_simple_graph, MPLValueType, MPLEntityClass, MPLClause, MPLRule, \
    rule_expression_to_simple_graph


def test_id_generator():
    line = MPLLine(1, 1, 'hello')
    other = [1, 'blah', 'gorp']
    id_0 = get_entity_id(line)
    id_1 = get_entity_id(line, *other)
    assert id_0 != id_1


def test_declaration_graph_construction():
    from interpreter.reference_resolution.reference_graph_resolution import MPLEntityClass as ec, MPLValueType as vt, MPLGraphEdgeType as et

    result = parse_machine_file('Tests/test_files/simple_machine_declaration_file.mpl')

    first_line = result.value[0]
    expected_line_entry = MPLLine(1, 0, 'base: machine')
    expected_machine_id = get_entity_id(expected_line_entry)
    expected_entity = MPLEntity(expected_machine_id, 'base', ec.MACHINE, vt.ANY, None)

    expected = SimpleGraph(
        verts={
            MPLLine(1, 0, 'base: machine'),
            Reference('base', None),
            Reference('base', 'machine'),
            expected_entity
        },
        edges={
            (Reference('base', None), et.DEFINED_BY, MPLLine(1, 0, 'base: machine')),
            (Reference('base', 'machine'), et.DEFINED_BY, MPLLine(1, 0, 'base: machine')),
            (Reference('base', None), et.QUALIFIED_BY, Reference('base', 'machine')),
            (Reference('base', 'machine'), et.INSTANTIATED_AS, expected_entity)

        }
    )

    actual, _, __ = declaration_expression_to_simple_graph(first_line, 1)

    assert actual == expected
    assert _ == MPLEntityClass.MACHINE
    assert __ == MPLValueType.ANY


def test_rule_graph_construction():
    from interpreter.reference_resolution.reference_graph_resolution import MPLGraphEdgeType as et

    expected_line_entry = MPLLine(14, 4, 'base state 2 -> test variable > 10 ->  complex state layer 2a')

    expected_clause_id = get_entity_id(expected_line_entry, 0)
    expected_clause_1 = MPLClause(expected_clause_id, quick_parse(StateExpression, 'base state 2'))

    expected_clause_id = get_entity_id(expected_line_entry, 1)
    expected_clause_2 = MPLClause(expected_clause_id, quick_parse(LogicalExpression, 'test variable > 10'))

    expected_clause_id = get_entity_id(expected_line_entry, 2)
    expected_clause_3 = MPLClause(expected_clause_id, quick_parse(StateExpression, 'complex state layer 2a'))

    expected_rule = MPLRule(
        get_entity_id(expected_line_entry),
        (expected_clause_1, expected_clause_2, expected_clause_3),
        (MPLOperator('ANY', 'CONSUME', 'STATE', 17), MPLOperator('ANY', 'CONSUME', 'STATE', 39))
    )

    expected = SimpleGraph(
        verts={
            expected_line_entry,
            Reference('base state 2', None),
            Reference('test variable', None),
            Reference('complex state layer 2a', None),
            expected_clause_1,
            expected_clause_2,
            expected_clause_3,
            expected_rule
        },
        edges={
            (Reference('base state 2', None), et.EVALUATED_IN, expected_clause_1),
            (Reference('test variable', None), et.EVALUATED_IN, expected_clause_2),
            (Reference('complex state layer 2a', None), et.EVALUATED_IN, expected_clause_3),
            (Reference('base state 2', None), et.CHANGED_IN, expected_clause_1),
            (Reference('complex state layer 2a', None), et.CHANGED_IN, expected_clause_3),
            (expected_clause_1, et.CHILD_OF, expected_rule),
            (expected_clause_2, et.CHILD_OF, expected_rule),
            (expected_clause_3, et.CHILD_OF, expected_rule),
        }
    )

    source = parse_machine_file('Tests/test_files/simple_machine_declaration_file.mpl')
    actual_line = source.value[13]
    actual = rule_expression_to_simple_graph(actual_line, 14)

    assert actual == expected


def test_rule_graph_construction_with_trigger():
    from interpreter.reference_resolution.reference_graph_resolution import MPLGraphEdgeType as et

    expected_line_entry = MPLLine(10, 4, 'Ok & <Turn Ended> ~> Turns Wounded > 0 ~@ Turns Wounded -= 1')

    expected_clause_id = get_entity_id(expected_line_entry, 0)
    expected_clause_1 = MPLClause(expected_clause_id, quick_parse(StateExpression, 'Ok & <Turn Ended>'))

    expected_clause_id = get_entity_id(expected_line_entry, 1)
    expected_clause_2 = MPLClause(expected_clause_id, quick_parse(LogicalExpression, 'Turns Wounded > 0'))

    expected_clause_id = get_entity_id(expected_line_entry, 2)
    expected_clause_3 = MPLClause(expected_clause_id, quick_parse(AssignmentExpression, 'Turns Wounded -= 1'))

    expected_rule = MPLRule(
        get_entity_id(expected_line_entry),
        (expected_clause_1, expected_clause_2, expected_clause_3),
        (MPLOperator('ANY', 'OBSERVE', 'STATE', 22), MPLOperator('ANY', 'OBSERVE', 'ACTION', 43))
    )

    expected = SimpleGraph(
        verts={
            expected_line_entry,
            Reference('Ok', None),
            Reference('Turn Ended', None),
            Reference('Turns Wounded', None),
            expected_clause_1,
            expected_clause_2,
            expected_clause_3,
            expected_rule
        },
        edges={
            (Reference('Ok', None), et.EVALUATED_IN, expected_clause_1),
            (Reference('Turn Ended', None), et.EVALUATED_IN, expected_clause_1),
            (Reference('Turns Wounded', None), et.EVALUATED_IN, expected_clause_2),
            (Reference('Turns Wounded', None), et.EVALUATED_IN, expected_clause_3),
            (Reference('Turns Wounded', None), et.CHANGED_IN, expected_clause_3),
            (expected_clause_1, et.CHILD_OF, expected_rule),
            (expected_clause_2, et.CHILD_OF, expected_rule),
            (expected_clause_3, et.CHILD_OF, expected_rule),
        }
    )

    source = parse_machine_file('Tests/test_files/simple_wumpus.mpl')
    actual_line = source.value[9]
    actual = rule_expression_to_simple_graph(actual_line, 10)

    assert actual == expected


def test_rule_graph_construction_with_scenario_and_void():
    from interpreter.reference_resolution.reference_graph_resolution import MPLGraphEdgeType as et

    expected_line_entry = MPLLine(36, 8, 'Hurt ~> Feel Secure -> %{Turns Wounded} -> *')

    expected_clause_id = get_entity_id(expected_line_entry, 0)
    expected_clause_1 = MPLClause(expected_clause_id, quick_parse(StateExpression, 'Hurt'))

    expected_clause_id = get_entity_id(expected_line_entry, 1)
    expected_clause_2 = MPLClause(expected_clause_id, quick_parse(StateExpression, 'Feel Secure'))

    expected_clause_id = get_entity_id(expected_line_entry, 2)
    expected_clause_3 = MPLClause(expected_clause_id, quick_parse(ScenarioExpression, '%{Turns Wounded}'))

    expected_clause_id = get_entity_id(expected_line_entry, 3)
    expected_clause_4 = MPLClause(expected_clause_id, quick_parse(StateExpression, '*'))

    expected_rule = MPLRule(
        get_entity_id(expected_line_entry),
        (expected_clause_1, expected_clause_2, expected_clause_3, expected_clause_4),
        (
            MPLOperator('ANY', 'OBSERVE', 'STATE', 13),
            MPLOperator('ANY', 'CONSUME', 'STATE', 28),
            MPLOperator('ANY', 'CONSUME', 'STATE', 48)
        )
    )

    expected = SimpleGraph(
        verts={
            expected_line_entry,
            Reference('Hurt', None),
            Reference('Feel Secure', None),
            Reference('Turns Wounded', None),
            Reference('void', None),
            expected_clause_1,
            expected_clause_2,
            expected_clause_3,
            expected_clause_4,
            expected_rule
        },
        edges={
            (Reference('Hurt', None), et.EVALUATED_IN, expected_clause_1),
            (Reference('Feel Secure', None), et.EVALUATED_IN, expected_clause_2),
            (Reference('Turns Wounded', None), et.EVALUATED_IN, expected_clause_3),
            (Reference('void', None), et.EVALUATED_IN, expected_clause_4),
            (Reference('Feel Secure', None), et.CHANGED_IN, expected_clause_2),
            (Reference('void', None), et.CHANGED_IN, expected_clause_4),
            (expected_clause_1, et.CHILD_OF, expected_rule),
            (expected_clause_2, et.CHILD_OF, expected_rule),
            (expected_clause_3, et.CHILD_OF, expected_rule),
            (expected_clause_4, et.CHILD_OF, expected_rule),
        }
    )

    source = parse_machine_file('Tests/test_files/simple_wumpus.mpl')
    actual_line = source.value[35]
    actual = rule_expression_to_simple_graph(actual_line, 36)

    assert sorted(list(actual.edges), key=repr) == sorted(list(expected.edges), key=repr)
    assert actual == expected


def test_rule_graph_construction_doesnt_fail_on_simple_wumpus_lines():
    source = parse_machine_file('Tests/test_files/simple_wumpus.mpl').value
    for i, line in enumerate(source):
        if isinstance(line, DeclarationExpression):
            actual, _, __ = declaration_expression_to_simple_graph(line, i+1)
        elif isinstance(line, RuleExpression):
            actual = rule_expression_to_simple_graph(line, i+1)


def test_graph_generation_for_simpler_wumpus_mpl():
    from interpreter.reference_resolution.reference_graph_resolution import MPLGraphEdgeType as et

    references = [
        ('Wumpus: machine', 1, 0),
        ('Health: state', 2, 4),
        ('Ok: state', 'Ok', 3, 8),
        ('Dead: state', 'Dead', 4, 8),
        ('Stab:trigger',),
        ('Activity: state', 10, 4),
        ('Wander: state', 'Wander',  11, 8),
        ('Attack: state', 'Attack', 12, 8),
        ('Flee: state', 'Flee', 13, 8),
        ('Mindset: machine', 17, 4),
        ('Smell Prey:state', 'Smell Prey', 18, 8),
        ('Feel Secure:state', 'Feel Secure', 19, 8),
        ('Snarl:trigger',),
        ('Enter Strike Zone:trigger',),
        ('Hunter Died:trigger',),
        ('noise:string',),
    ]

    ref_child_edges = [
        (('Health', 'Activity', 'Mindset'), et.CHILD_OF, 'Wumpus'),
        (('Ok', 'Dead'), (et.CHILD_OF, et.EXCLUSIVE_CHILD_OF), 'Health'),
        (('Wander', 'Attack', 'Flee'), (et.CHILD_OF, et.EXCLUSIVE_CHILD_OF), 'Activity'),
        (('Smell Prey', 'Feel Secure', 'Snarl'), et.CHILD_OF, 'Mindset'),
        (('Stab', 'Enter Strike Zone', 'Hunter Died', 'noise'), et.CHILD_OF, 'Wumpus'),
    ]

    rule_verts = [
        (
            ('* ~> Ok', 6, 4,),
            [
                (StateExpression, '*', ('void',)),
                (StateExpression, 'Ok', ('Ok',)),
            ],
            ('~>',)
        ),
        (
            ('<Stab> ~> Ok -> Dead', 8, 4,),
            [
                (StateExpression, '<Stab>', ('Stab',)),
                (StateExpression, 'Ok', ('Ok',)),
                (StateExpression, 'Dead', ('Dead',)),
            ],
            ('~>', '->')
        ),
        (
            ('* ~> Wander', 15, 4,),
            [
                (StateExpression, '*', ('void',)),
                (StateExpression, 'Wander', ('Wander',)),
            ],
            ('~>')
        ),
        (
            ('Distance To Prey < Smell Range -> Smell Prey', 21, 8,),
            [
                (LogicalExpression, 'Distance To Prey < Smell Range', ('Distance To Prey', 'Smell Range',)),
                (StateExpression, 'Smell Prey', ('Smell Prey',)),
            ],
            ('->',)
        ),
        (
            ('Distance To Prey < Smell Range -> <Snarl>', 22, 8,),
            [
                (LogicalExpression, 'Distance To Prey < Smell Range', ('Distance To Prey', 'Smell Range',)),
                (StateExpression, '<Snarl>', ('Snarl',)),
            ],
            ('->',)
        ),
        (
            ('Distance To Prey > Smell Range -> Smell Prey -> *', 24, 8,),
            [
                (LogicalExpression, 'Distance To Prey > Smell Range', ('Distance To Prey', 'Smell Range',)),
                (StateExpression, 'Smell Prey', ('Smell Prey',)),
                (StateExpression, '*', ('void',)),
            ],
            ('->', '->')
        ),
        (
            ('* & Ok ~> Feel Secure', 26, 8,),
            [
                (StateExpression, '* & Ok', ('void', 'Ok',)),
                (StateExpression, 'Feel Secure', ('Feel Secure',)),
            ],
            ('~>',)
        ),

    ]

    # TODO: Continue from line 28
