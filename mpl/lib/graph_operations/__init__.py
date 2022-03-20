from typing import Any, Iterable

import networkx as nx
from networkx import Graph, MultiDiGraph


def graph_to_edge_set(graph: Graph) -> set:
    """
    Converts a graph to an edge set.
    :param graph: Graph to convert.
    :return: Edge set.
    """
    edges = graph.edges(data=True)
    formatted = {(u, v, tuple(d.items())) for u, v, d in edges}
    return set(formatted)


def edge_set_to_graph(edge_set: set) -> MultiDiGraph:
    """
    Converts an edge set to a graph.
    :param edge_set: Edge set to convert.
    :return: Graph.
    """
    edge_list = [(u, v, dict(d)) for u, v, d in edge_set]
    result = nx.MultiDiGraph()
    result.add_edges_from(edge_list)
    return result


def combine_graphs(a: Graph, b: Graph) -> MultiDiGraph:
    """
    Combines two graphs.
    :param a: First graph.
    :param b: Second graph.
    :return: Combined graph.
    """
    set_a = graph_to_edge_set(a)
    set_b = graph_to_edge_set(b)
    combined = set_a | set_b
    result = edge_set_to_graph(combined)
    return result


def drop_from_graph(node: Any, graph: Graph) -> MultiDiGraph:
    """
    Removes a node from a graph.
    :param node: Node to remove.
    :param graph: Graph to remove from.
    :return: Graph without the node.
    """

    if not isinstance(node, Iterable):
        node = {node}

    edge_set = graph_to_edge_set(graph)
    dropped = {(u, v, d) for u, v, d in edge_set if not node & {u, v}}
    result = edge_set_to_graph(dropped)
    return result
