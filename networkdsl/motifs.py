"""Motif constructors and graph composition utilities for the DSL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Tuple

from .types import Graph, NodeId, NodeSet, make_edge

Bridge = Tuple[NodeId, NodeId]

__all__ = [
    "DegreeCriteria",
    "ring",
    "path",
    "star",
    "mesh",
    "overlay",
    "connect",
    "relabel",
    "pick",
    "require",
]


@dataclass(frozen=True, slots=True)
class DegreeCriteria:
    """Criteria that selects nodes with an exact degree."""

    degree: int

    def __post_init__(self) -> None:
        if self.degree < 0:
            raise ValueError("Degree criteria must be non-negative.")


def ring(n: int) -> Graph:
    if n < 3:
        raise ValueError("Ring motif requires n >= 3.")
    edges = {make_edge(i, (i + 1) % n) for i in range(n)}
    return Graph(n, frozenset(edges))


def path(n: int) -> Graph:
    if n < 2:
        raise ValueError("Path motif requires n >= 2.")
    edges = {make_edge(i, i + 1) for i in range(n - 1)}
    return Graph(n, frozenset(edges))


def star(k: int) -> Graph:
    if k < 2:
        raise ValueError("Star motif requires k >= 2.")
    edges = {make_edge(0, i) for i in range(1, k)}
    return Graph(k, frozenset(edges))


def mesh(n: int) -> Graph:
    if n < 1:
        raise ValueError("Mesh motif requires n >= 1.")
    edges = {
        make_edge(i, j)
        for i in range(n)
        for j in range(i + 1, n)
    }
    return Graph(n, frozenset(edges))


def overlay(g1: Graph, g2: Graph) -> Graph:
    offset = g1.node_count
    shifted = {make_edge(u + offset, v + offset) for u, v in g2.edges}
    combined = set(g1.edges)
    combined.update(shifted)
    return Graph(g1.node_count + g2.node_count, frozenset(combined))


def connect(g1: Graph, g2: Graph, *, bridge: Bridge) -> Graph:
    local_u, local_v = bridge
    if not g1.has_node(local_u):
        raise ValueError(f"Bridge source node {local_u} is not in the first graph.")
    if not g2.has_node(local_v):
        raise ValueError(f"Bridge target node {local_v} is not in the second graph.")

    base = overlay(g1, g2)
    offset_v = local_v + g1.node_count
    return base.with_extra_edges([(local_u, offset_v)])


def relabel(graph: Graph, mapping: Mapping[NodeId, NodeId]) -> Graph:
    return graph.relabel(mapping)


def pick(graph: Graph, criteria: DegreeCriteria) -> NodeSet:
    matching = {node for node in range(graph.node_count) if graph.degree(node) == criteria.degree}
    return NodeSet(frozenset(matching))


def require(condition: bool, message: str | None = None) -> bool:
    if not condition:
        raise ValueError(message or "Requirement failed.")
    return True

