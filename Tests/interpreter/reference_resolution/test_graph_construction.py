from typing import Tuple

from mpl.Parser.ExpressionParsers.arithmetic_expression_parser import ArithmeticExpression
from mpl.Parser.ExpressionParsers.assignment_expression_parser import AssignmentExpression
from mpl.Parser.ExpressionParsers.query_expression_parser import QueryExpression
from mpl.Parser.ExpressionParsers.machine_expression_parser import parse_machine_file
from mpl.Parser.ExpressionParsers.reference_expression_parser import Reference, DeclarationExpression, ReferenceExpression
from mpl.Parser.ExpressionParsers.rule_expression_parser import RuleExpression
from mpl.Parser.ExpressionParsers.scenario_expression_parser import ScenarioExpression

from mpl.Parser.ExpressionParsers.state_expression_parser import StateExpression
from mpl.Parser.Tokenizers.operator_tokenizers import MPLOperator
from Tests import quick_parse

from mpl.lib.simple_graph import SimpleGraph
from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLLine, MPLEntity, get_entity_id, \
    declaration_expression_to_simple_graph, MPLEntityClass, MPLClause, MPLRule, \
    rule_expression_to_simple_graph, complex_expression_to_reference_graph, MPLGraphEdgeType, \
    mpl_file_lines_to_simple_graph, reference_to_simple_graph, expression_with_metadata_to_mpl_line


def test_id_generator():
    line = MPLLine(1, 1, 'hello')
    other = [1, 'blah', 'gorp']
    id_0 = get_entity_id(line)
    id_1 = get_entity_id(line, *other)
    assert id_0 != id_1


def test_declaration_graph_construction():
    from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLEntityClass as ec, MPLGraphEdgeType as et

    result = parse_machine_file('Tests/test_files/simple_machine_declaration_file.mpl')

    first_line = result[0]
    expected_line_entry = MPLLine(1, 0, 'base: machine')
    expected_machine_id = get_entity_id(expected_line_entry)
    expected_entity = MPLEntity(expected_machine_id, 'base', ec.MACHINE, None)

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

    actual, _ = declaration_expression_to_simple_graph(first_line, MPLLine(1, 0, 'base: machine'))

    assert actual == expected
    assert _ == MPLEntityClass.MACHINE


def test_rule_graph_construction():
    from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLGraphEdgeType as et

    expected_line_entry = MPLLine(14, 4, 'base state 2 -> test variable > 10 ->  complex state layer 2a')

    expected_clause_id = get_entity_id(expected_line_entry, 0)
    expected_clause_1 = MPLClause(expected_clause_id, quick_parse(StateExpression, 'base state 2'))

    expected_clause_id = get_entity_id(expected_line_entry, 1)
    expected_clause_2 = MPLClause(expected_clause_id, quick_parse(QueryExpression, 'test variable > 10'))

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
    actual_line = source[13]
    line = expression_with_metadata_to_mpl_line(actual_line, 14)
    actual_graph, actual_rule = rule_expression_to_simple_graph(actual_line, line)

    actual_graph_tuple, expected_graph_tuple = get_comparable_simplegraphs(actual_graph, expected)
    assert actual_graph_tuple[0] == expected_graph_tuple[0]
    assert actual_graph_tuple[1] == expected_graph_tuple[1]


def get_simplegraph_as_tuple(graph: SimpleGraph):
    verts = sorted(list(graph.vertices), key=repr)
    edges = sorted(list(graph.edges), key=repr)
    return tuple(verts), tuple(edges)


def get_comparable_simplegraphs(actual:SimpleGraph, expected:SimpleGraph) -> Tuple:
    return  get_simplegraph_as_tuple(actual), get_simplegraph_as_tuple(expected)


def test_rule_graph_construction_with_trigger():
    from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLGraphEdgeType as et

    expected_line_entry = MPLLine(10, 4, 'Ok & <Turn Ended> ~> Turns Wounded > 0 ~@ Turns Wounded -= 1')

    expected_clause_id = get_entity_id(expected_line_entry, 0)
    expected_clause_1 = MPLClause(expected_clause_id, quick_parse(StateExpression, 'Ok & <Turn Ended>'))

    expected_clause_id = get_entity_id(expected_line_entry, 1)
    expected_clause_2 = MPLClause(expected_clause_id, quick_parse(QueryExpression, 'Turns Wounded > 0'))

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
            Reference('Turns Wounded', None),
            Reference('Turn Ended', None),
            Reference('Turn Ended', 'trigger'),
            expected_clause_1,
            expected_clause_2,
            expected_clause_3,
            expected_rule
        },
        edges={
            (Reference('Ok', None), et.EVALUATED_IN, expected_clause_1),
            (Reference('Turns Wounded', None), et.EVALUATED_IN, expected_clause_2),
            (Reference('Turns Wounded', None), et.EVALUATED_IN, expected_clause_3),
            (Reference('Turns Wounded', None), et.CHANGED_IN, expected_clause_3),
            (Reference('Turn Ended', 'trigger'), et.EVALUATED_IN, expected_clause_1),
            (Reference(name='Turn Ended', type=None), et.EVALUATED_IN, expected_clause_1),
            (Reference(name='Turn Ended', type=None), et.QUALIFIED_BY, Reference('Turn Ended', 'trigger')),
            (expected_clause_1, et.CHILD_OF, expected_rule),
            (expected_clause_2, et.CHILD_OF, expected_rule),
            (expected_clause_3, et.CHILD_OF, expected_rule),
        }
    )

    source = parse_machine_file('Tests/test_files/simple_wumpus.mpl')
    actual_line = source[9]

    mpl_line = expression_with_metadata_to_mpl_line(actual_line, 10)
    actual_graph, rule = rule_expression_to_simple_graph(actual_line, mpl_line)

    actual_graph_tuple, expected_graph_tuple = get_comparable_simplegraphs(actual_graph, expected)
    assert actual_graph_tuple[0] == expected_graph_tuple[0]
    assert actual_graph_tuple[1] == expected_graph_tuple[1]


def test_rule_graph_construction_with_scenario_and_void():
    from mpl.interpreter.reference_resolution.reference_graph_resolution import MPLGraphEdgeType as et

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
    line_expression = source[35]
    actual_line = expression_with_metadata_to_mpl_line(line_expression, 36)
    actual, rule = rule_expression_to_simple_graph(line_expression, actual_line)

    assert sorted(list(actual.edges), key=repr) == sorted(list(expected.edges), key=repr)
    assert actual == expected


def test_complex_expression_to_reference_graph():

    expectations = {
        quick_parse(ArithmeticExpression, 'a+b+(5-c)'): SimpleGraph(
            {
                Reference(name='b', type=None),
                Reference(name='c', type=None),
                Reference(name='a', type=None)
            },
            set()
        ),
        quick_parse(StateExpression, '<Notice me> & Senpai'): SimpleGraph(
            {
                Reference(name='Notice me', type=None),
                Reference(name='Notice me', type='trigger'),
                Reference(name='Senpai', type=None),
            },
            edges={
                (
                    Reference(name='Notice me', type=None),
                    MPLGraphEdgeType.QUALIFIED_BY,
                    Reference(name='Notice me', type='trigger')
                )
            }

        ),
    }

    for input in expectations:
        actual = complex_expression_to_reference_graph(input)
        expected = expectations[input]
        assert actual == expected


def test_rule_graph_construction_doesnt_fail_on_simple_wumpus_lines():
    source = parse_machine_file('Tests/test_files/simple_wumpus.mpl')
    for i, line in enumerate(source):
        if isinstance(line, DeclarationExpression):
            actual, _= declaration_expression_to_simple_graph(line, i+1)
        elif isinstance(line, RuleExpression):
            actual = rule_expression_to_simple_graph(line, i+1)


def quick_digest_file_to_mpllines(path):
    with open(path) as f:
        content = f.read()

    lines = content.split('\n')
    out = []
    for index, line in enumerate(lines):
        source = line.strip()
        depth = len(line) - len(source)
        out.append(
            MPLLine(index + 1, depth, source)
        )

    return out


def test_graph_generation_by_edge_type_defined_by_and_qualified_by():
    test_file = 'Tests/test_files/simpler_wumpus.mpl'
    file_mpl_lines = quick_digest_file_to_mpllines(test_file)

    declared_references = [
        (quick_parse(ReferenceExpression, 'Wumpus: machine'), 1,),
        (quick_parse(ReferenceExpression, 'Health: state'), 2,),
        (quick_parse(ReferenceExpression, 'Ok: state'), 3,),
        (quick_parse(ReferenceExpression, 'Dead: state'), 4,),
        (quick_parse(ReferenceExpression, 'Activity: state'), 10,),
        (quick_parse(ReferenceExpression, 'Wander: state'), 11,),
        (quick_parse(ReferenceExpression, 'Attack: state'), 12,),
        (quick_parse(ReferenceExpression, 'Flee: state'), 13,),
        (quick_parse(ReferenceExpression, 'Mindset: machine'), 17,),
        (quick_parse(ReferenceExpression, 'Smell Prey: state'), 18,),
        (quick_parse(ReferenceExpression, 'Feel Secure: state'), 19,),
        (quick_parse(ReferenceExpression, 'Stab: trigger'),),
        (quick_parse(ReferenceExpression, 'Snarl: trigger'),),
        (quick_parse(ReferenceExpression, 'noise: any'),),
        (quick_parse(ReferenceExpression, 'Distance To Prey: any'),),
        (quick_parse(ReferenceExpression, 'Smell Range: any'),),
    ]
    expected = SimpleGraph()

    for ref in declared_references:
        ref_graph = reference_to_simple_graph(ref[0].value)
        v: Reference
        definition_edges = set()
        for line_number in ref[1:]:
            line: MPLLine
            source_line = [line for line in file_mpl_lines if line.line_number == line_number][0]
            for vert in ref_graph.vertices:
                tmp_edge = (vert, MPLGraphEdgeType.DEFINED_BY, source_line)
                definition_edges.add(tmp_edge)
        ref_graph.edges |= definition_edges
        expected |= ref_graph

    parse_results = parse_machine_file(test_file)
    actual = mpl_file_lines_to_simple_graph(parse_results)

    actual_graph_tuple, expected_graph_tuple = get_comparable_simplegraphs(actual, expected)

    for v in expected.vertices:
        assert v in actual.vertices

    for e in expected.edges:
        assert e in actual.edges


def test_graph_generation_by_edge_type_child_of_and_exclusive_child_of():
    test_file = 'Tests/test_files/simpler_wumpus.mpl'

    parse_results = parse_machine_file(test_file)
    actual = mpl_file_lines_to_simple_graph(parse_results)

    expected_edges = [
        (
            Reference('Wander', 'state'),
            MPLGraphEdgeType.EXCLUSIVE_CHILD_OF,
            Reference('Activity', 'state')
        ),
        (
            Reference('Dead', 'state'),
            MPLGraphEdgeType.EXCLUSIVE_CHILD_OF,
            Reference('Health', 'state')
        ),
        (
            Reference('Activity', 'state'),
            MPLGraphEdgeType.CHILD_OF,
            Reference('Wumpus', 'machine')
        ),
    ]

    for edge in expected_edges:
        assert edge in actual


def test_graph_generation_assorted_edge_checks():
    from typing import Any

    test_file = 'Tests/test_files/simpler_wumpus.mpl'

    parse_results = parse_machine_file(test_file)
    actual:SimpleGraph = mpl_file_lines_to_simple_graph(parse_results)

    expected_edges = [
        (
            (Reference('noise', 'any'), MPLGraphEdgeType.CHANGED_IN, MPLClause), 2
        ),
        (
            (Reference('Feel Secure', 'state'), MPLGraphEdgeType.CHANGED_IN, MPLClause), 4
        ),
        (
            (
                Reference('Wumpus', 'machine'),
                MPLGraphEdgeType.INSTANTIATED_AS,
                MPLEntity(Any, 'Wumpus', MPLEntityClass.MACHINE, Any)
            ), 1
        ),
        (
            (
                Reference('Wander', 'state'),
                MPLGraphEdgeType.INSTANTIATED_AS,
                MPLEntity(Any, 'Wander', MPLEntityClass.STATE, Any)
            ), 1
        ),
        (
            (
                Reference('noise', 'any'),
                MPLGraphEdgeType.INSTANTIATED_AS,
                MPLEntity(Any, 'noise', MPLEntityClass.VARIABLE, Any)
            ), 1
        ),
        (
            (
                Reference('Snarl', 'trigger'),
                MPLGraphEdgeType.INSTANTIATED_AS,
                MPLEntity(Any, 'Snarl', MPLEntityClass.TRIGGER, Any)
            ), 1
        ),
    ]

    for expectation in expected_edges:
        result = actual.filter(expectation[0])
        assert len(result) == expectation[1]
