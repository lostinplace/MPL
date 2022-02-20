import dataclasses
import enum
from typing import Set, Iterable, Any, Tuple, Union

from mpl.lib.quick_filter_set import filter_set


class SimpleGraphFilterType(enum.Flag):
    VERTICES = enum.auto()
    EDGES = enum.auto()
    ANY = VERTICES | EDGES


#TODO: This should be unified, edges and vertices should be one collection


@dataclasses.dataclass
class SimpleGraph:
    vertices: Set
    edges: Set

    def __init__(self, verts: Iterable[Any] = set(), edges:Iterable[Tuple[Any, Any, Any]] = set()):
        self.vertices = set(verts or [])
        self.edges = set(edges or [])

    def __or__(self, other):
        from collections.abc import Iterable

        if isinstance(other, SimpleGraph):
            tmp_v = self.vertices | other.vertices
            tmp_e = self.edges | other.edges
        elif isinstance(other, Iterable):
            tmp_v = self.vertices | set(other[0])
            tmp_e = self.edges | set(other[1])
        else:
            raise TypeError('must be simplegraph or two-iteem iterable')

        return SimpleGraph(tmp_v, tmp_e)

    def __ior__(self, other):
        result = self | other
        return result

    def __contains__(self, item):
        return (item in self.edges) or (item in self.vertices)

    def filter(self, filter, source: SimpleGraphFilterType = SimpleGraphFilterType.ANY) -> Set[Any]:
        sgft = SimpleGraphFilterType
        result = set()
        if source & sgft.VERTICES:
            result |= filter_set(self.vertices, filter)
        if source & sgft.EDGES:
            result |= filter_set(self.edges, filter)

        return result

    def add(self, item: Union[Any, Tuple[Any, Any, Any]]):
        if isinstance(item, Tuple) and len(item) == 3:
            self.edges.add(item)
        else:
            self.vertices.add(item)

    def __iter__(self, source: SimpleGraphFilterType = SimpleGraphFilterType.ANY):
        sgft = SimpleGraphFilterType
        result = set()

        if source & sgft.VERTICES:
            result |= self.vertices
        if source & sgft.EDGES:
            result |= self.edges

        for item in result:
            yield item


Edge = Tuple[Any, Any, Any]
Vertex = Any


@dataclasses.dataclass(frozen=True, order=True)
class Traversal:
    source: Vertex
    path: Edge
    destination: Vertex


def simple_graph_traverse(graph: SimpleGraph, source_filter = Any, edge_filter: Edge = (Any, Any, Any)) \
        -> Tuple[Traversal]:
    results = list()
    source_verts = filter_set(graph.vertices, source_filter)

    for vert in source_verts:
        first_edge_filter = (vert, edge_filter[1], edge_filter[2])
        active_edges = filter_set(graph.edges, first_edge_filter)
        active_edges = filter_set(active_edges, edge_filter)
        for edge in active_edges:
            results.append(Traversal(vert, edge, edge[2]))

    return tuple(results)

