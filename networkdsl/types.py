"""Core type definitions for the network topology DSL."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterable, Iterator, Mapping, Set, Tuple

NodeId = int
Edge = Tuple[NodeId, NodeId]
EdgeSet = FrozenSet[Edge]

__all__ = ["NodeId", "Edge", "EdgeSet", "NodeRef", "NodeSet", "Graph", "make_edge"]


def _normalize_edge(u: NodeId, v: NodeId) -> Edge:
    if u == v:
        raise ValueError("Self-loops are not permitted in this graph DSL.")
    if u < v:
        return (u, v)
    return (v, u)


@dataclass(frozen=True, slots=True)
class NodeRef:
    """Qualified reference to a node produced by an intermediate binding."""

    ident: str
    index: NodeId

    def __post_init__(self) -> None:
        if not self.ident:
            raise ValueError("NodeRef.ident must be a non-empty identifier.")
        if self.index < 0:
            raise ValueError("NodeRef.index must be non-negative.")


@dataclass(frozen=True, slots=True)
class NodeSet:
    """Immutable wrapper representing a set of node identifiers."""

    nodes: FrozenSet[NodeId] = field(default_factory=frozenset)

    def __iter__(self) -> Iterator[NodeId]:
        return iter(self.nodes)

    def __len__(self) -> int:
        return len(self.nodes)

    def union(self, other: "NodeSet") -> "NodeSet":
        return NodeSet(self.nodes.union(other.nodes))

    def intersection(self, other: "NodeSet") -> "NodeSet":
        return NodeSet(self.nodes.intersection(other.nodes))


@dataclass(frozen=True, slots=True)
class Graph:
    """Simple immutable undirected graph used throughout the DSL."""

    node_count: int
    edges: EdgeSet = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.node_count < 0:
            raise ValueError("Graphs must contain a non-negative number of nodes.")

        normalized_edges: Set[Edge] = set()
        for edge in self.edges:
            if len(edge) != 2:
                raise ValueError(f"Edges must contain two node ids, received {edge!r}.")
            u, v = edge
            if not (0 <= u < self.node_count) or not (0 <= v < self.node_count):
                raise ValueError(
                    f"Edge {edge!r} references node outside the range 0..{self.node_count - 1}."
                )
            normalized_edges.add(_normalize_edge(u, v))

        object.__setattr__(self, "edges", frozenset(normalized_edges))

    def has_node(self, node: NodeId) -> bool:
        return 0 <= node < self.node_count

    def has_edge(self, u: NodeId, v: NodeId) -> bool:
        if not self.has_node(u) or not self.has_node(v):
            return False
        return _normalize_edge(u, v) in self.edges

    def neighbors(self, node: NodeId) -> FrozenSet[NodeId]:
        if not self.has_node(node):
            raise ValueError(f"Node {node} is not present in this graph.")
        adjacent = {v if u == node else u for u, v in self.edges if node in (u, v)}
        return frozenset(adjacent)

    def degree(self, node: NodeId) -> int:
        return len(self.neighbors(node))

    def with_extra_edges(self, edges: Iterable[Tuple[NodeId, NodeId]]) -> "Graph":
        normalized = set(self.edges)
        for u, v in edges:
            if not self.has_node(u) or not self.has_node(v):
                raise ValueError(f"Edge ({u}, {v}) references unknown node.")
            normalized.add(_normalize_edge(u, v))
        return Graph(self.node_count, frozenset(normalized))

    def relabel(self, mapping: Mapping[NodeId, NodeId]) -> "Graph":
        if not mapping:
            return self

        if any(node < 0 or node >= self.node_count for node in mapping.keys()):
            raise ValueError("Relabel mapping contains unknown source node ids.")

        targets = list(mapping.values())
        if any(target < 0 or target >= self.node_count for target in targets):
            raise ValueError("Relabel mapping targets must remain within node range.")
        if len(set(targets)) != len(targets):
            raise ValueError("Relabel mapping must be injective.")

        def remap(node: NodeId) -> NodeId:
            return mapping.get(node, node)

        new_edges = {
            _normalize_edge(remap(u), remap(v))
            for u, v in self.edges
        }
        return Graph(self.node_count, frozenset(new_edges))


def make_edge(u: NodeId, v: NodeId) -> Edge:
    """Create a normalized undirected edge."""
    return _normalize_edge(u, v)

