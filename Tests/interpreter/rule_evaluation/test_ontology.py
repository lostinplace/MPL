from random import Random

import networkx as nx

from mpl.Parser.ExpressionParsers.machine_expression_parser import MachineFile
from mpl.Parser.ExpressionParsers.reference_expression_parser import Ref

from mpl.interpreter.reference_resolution.mpl_ontology import process_machine_file, get_current_path, PathInfo, \
    get_edges_by_type, Relationship, engine_to_string
from mpl.interpreter.expression_evaluation.entity_value import EntityValue

"""
edge_types:
{v} *is a* RULE | MACHINE | STATE | {v}:ENTITY
{v}:RULE *runs in* {v}:ENTITY
{v}:RULE *uses* {v}:ENTITY
{v}:ENTITY *defined in* {v}:ENTITY

Wumpus: machine
    Health: state
        Ok
        Hurt
        Dead

    * ~> Health.Ok

    Health.Hurt & <Turn Ended> ~@ Turns Wounded += 1
    Health.Ok & <Turn Ended> ~> Turns Wounded > 0 ~@ Turns Wounded -= 1

MPLE(Wumpus) is a MACHINE
MPLE(Wumpus.Health) is a STATE
MPLE(Wumpus.Health) defined in MPLE(Wumpus)

MPLE(Wumpus.Health.Ok) is a STATE
MPLE(Wumpus.Health.Ok) defined in MPLE(Wumpus.Health)
MPLE(Wumpus.Health.Hurt) is a STATE
MPLE(Wumpus.Health.Hurt) defined in MPLE(Wumpus.Health)
MPLE(Wumpus.Health.Dead) is a STATE
MPLE(Wumpus.Health.Dead) defined in MPLE(Wumpus.Health)

RE(Wumpus.* ~> Wumpus.Health.Ok) is a RULE
MPLE(Wumpus.*) defined in MPLE(Wumpus)
RE(Wumpus.* ~> Wumpus.Health.Ok) runs in MPLE(Wumpus)
RE(Wumpus.* ~> Wumpus.Health.Ok) uses MPLE(Wumpus.Health.Ok)
RE(Wumpus.* ~> Wumpus.Health.Ok) uses MPLE(Wumpus.*)

RE(Wumpus.Health.Hurt & <Wumpus.Turn Ended> ~@ Wumpus.Turns Wounded += 1) is a RULE
RE(Wumpus.Health.Hurt & <Wumpus.Turn Ended> ~@ Wumpus.Turns Wounded += 1) runs in MPLE(Wumpus)
MPLE(Wumpus.Turn Ended) defined in MPLE(Wumpus)
MPLE(Wumpus.Turns Wounded) defined in MPLE(Wumpus)
RE(Wumpus.Health.Hurt & <Wumpus.Turn Ended> ~@ Wumpus.Turns Wounded += 1) uses MPLE(Wumpus.Health.Hurt)

RE(Wumpus.Health.Hurt & <Wumpus.Turn Ended> ~@ Wumpus.Turns Wounded += 1) uses MPLE(Wumpus.Turn Ended)
RE(Wumpus.Health.Hurt & <Wumpus.Turn Ended> ~@ Wumpus.Turns Wounded += 1) uses MPLE(Wumpus.Turns Wounded)

"""


def test_context_generation():
    machine_file = MachineFile.from_file('Tests/test_files/simple_wumpus.mpl')
    assert machine_file.lines
    context, graph = process_machine_file(machine_file)
    assert Ref('Wumpus.Health.Ok') in context
    eege_list = graph.edges(data='relationship')
    x = filter(lambda x: x[0] == Ref('Wumpus.Health') or x[1] == Ref('Wumpus.Health'), eege_list)
    x = list(x)
    assert graph.has_edge(Ref('Wumpus.Health'), Ref('Wumpus'))
    assert context


def test_context_generation_with_context():
    machine_file = MachineFile.from_file('Tests/test_files/simplest.mpl')
    context, graph = process_machine_file(machine_file)
    assert context[Ref('One')] == EntityValue('One', frozenset({1}))



def test_combinations():
    from itertools import compress, product

    def combinations(items):
        masks = product(*[[0, 1]] * len(items))
        compressor = lambda x: compress(items, x)
        compressed = map(compressor, masks)
        as_sets = map(set, compressed)
        return as_sets

    a = combinations({1, 2, 3})
    print(list(a))


def test_path_determiner_insert_middle():
    heirarchy = ('a', 'b', 'c', 'd')
    depths = (0, 10, 20, 30)
    actual = get_current_path('new', 15, PathInfo(heirarchy, depths))
    assert actual == PathInfo(('a', 'b', 'new'), (0, 10, 15), ('a', 'b'))


def test_path_determiner_insert_middle_multi():
    heirarchy = ('a', 'b', 'c', 'd')
    depths = (0, 10, 20, 30)
    new_path = ('x', 'y', 'z')
    actual = get_current_path(new_path, 15, PathInfo(heirarchy, depths))
    assert actual == PathInfo(('a', 'b', 'x', 'y', 'z'), (0, 10, 15, 15, 15), ('a', 'b'))


def test_path_determiner_insert_start():
    existing_path = PathInfo(('a', 'b', 'c', 'd'), (0, 10, 20, 30))
    actual = get_current_path('new', 0, existing_path)
    assert actual == PathInfo(('new', ), (0, ), ())


def test_path_determiner_insert_end():
    existing_path = PathInfo(('a', 'b', 'c', 'd'), (0, 10, 20, 30))

    actual = get_current_path('new', 40, existing_path)
    expected = PathInfo(('a', 'b', 'c', 'd', 'new'), (0, 10, 20, 30, 40), ('a', 'b', 'c', 'd'))
    assert actual == expected


def test_path_determiner_insert_empty():
    actual = get_current_path('new', 40, None)
    assert actual == PathInfo(('new', ), (40, ), ())


def test_graph_contruction():
    G = nx.MultiDiGraph()  # or DiGraph, MultiGraph, MultiDiGraph, etc
    data = {"test":1}
    G.add_edge(0,1 , type='test')
    G.add_edge(0, 1, type='test 2')
    G.add_edge(0, 1, type='test 3')
    out =  G.predecessors(1)
    out_list = list(out)
    assert len(out_list) == 1
    out = get_edges_by_type(G, 'test 2')
    out_list = list(out)
    assert len(out_list) == 1


def test_engine_to_string():
    from mpl.interpreter.rule_evaluation.mpl_engine import MPLEngine

    test_files = [
        'Tests/test_files/simple_wumpus.mpl',
        'Tests/test_files/simplest.mpl',
    ]

    for test_file in test_files:
        original_engine = MPLEngine.from_file(test_file)
        rnd = Random(0)
        key = rnd.choice(list(original_engine.context.keys()))
        original_engine.activate(key)

        content = engine_to_string(original_engine)
        mf = MachineFile.parse(content)
        new_engine = MPLEngine.from_file(mf)
        assert original_engine.context == new_engine.context
        assert original_engine.rule_interpreters == new_engine.rule_interpreters
        original_graph = set(original_engine.graph.edges(data='relationship'))
        new_graph = set(new_engine.graph.edges(data='relationship'))
        assert original_graph == new_graph
        assert hash(original_engine) == hash(new_engine)


