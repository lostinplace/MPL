import dataclasses
from typing import Set, Iterable

@dataclasses.dataclass
class SimpleGraph:
    vertices: Set
    edges: Set

    def __init__(self, verts: Iterable= None, edges:Iterable = None):
        self.vertices = set(verts or [])
        self.edges = set(edges or [])

    def __or__(self, other ):
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