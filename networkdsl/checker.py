"""Static semantics for the network topology DSL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional

from . import ast
from .motifs import mesh, path, ring, star

__all__ = ["TypeTag", "GraphShape", "TypeInfo", "CheckResult", "Checker", "CheckError"]


class CheckError(ValueError):
    pass


class TypeTag(Enum):
    GRAPH = auto()
    NODESET = auto()
    BOOL = auto()


@dataclass(frozen=True, slots=True)
class GraphShape:
    node_count: int


@dataclass(frozen=True, slots=True)
class TypeInfo:
    tag: TypeTag
    graph: Optional[GraphShape] = None

    def ensure_graph(self) -> GraphShape:
        if self.tag != TypeTag.GRAPH or self.graph is None:
            raise CheckError("Expression is not a graph.")
        return self.graph


@dataclass(frozen=True, slots=True)
class CheckResult:
    final: Optional[TypeInfo]
    environment: Dict[str, TypeInfo]


class Checker:
    def __init__(self) -> None:
        self._env: Dict[str, TypeInfo] = {}

    def check(self, program: ast.Program) -> CheckResult:
        self._env.clear()
        for statement in program.statements:
            result = self._check_expression(statement.expression)
            if result.tag != TypeTag.GRAPH:
                raise CheckError(
                    f"Let binding '{statement.name}' must produce a Graph, found {result.tag.name}."
                )
            self._env[statement.name] = result

        final_info: Optional[TypeInfo] = None
        if program.expression is not None:
            final_info = self._check_expression(program.expression)
        return CheckResult(final_info, dict(self._env))

    def _check_expression(self, node: ast.Expression) -> TypeInfo:
        if isinstance(node, ast.MotifExpr):
            return self._check_motif(node)
        if isinstance(node, ast.IdentifierExpr):
            return self._check_identifier(node)
        if isinstance(node, ast.OverlayExpr):
            return self._check_overlay(node)
        if isinstance(node, ast.ConnectExpr):
            return self._check_connect(node)
        if isinstance(node, ast.RelabelExpr):
            return self._check_relabel(node)
        if isinstance(node, ast.PickExpr):
            return self._check_pick(node)
        if isinstance(node, ast.RequireExpr):
            return self._check_require(node)
        raise CheckError(f"Unsupported expression node: {type(node).__name__}")

    def _check_motif(self, node: ast.MotifExpr) -> TypeInfo:
        size = node.size
        try:
            graph = self._evaluate_motif(node.kind, size)
        except ValueError as error:
            raise CheckError(str(error)) from error
        return TypeInfo(TypeTag.GRAPH, GraphShape(graph.node_count))

    def _check_identifier(self, node: ast.IdentifierExpr) -> TypeInfo:
        info = self._env.get(node.name)
        if info is None:
            raise CheckError(f"Unknown identifier '{node.name}'.")
        return info

    def _check_overlay(self, node: ast.OverlayExpr) -> TypeInfo:
        left_info = self._check_expression(node.left)
        right_info = self._check_expression(node.right)
        left_shape = left_info.ensure_graph()
        right_shape = right_info.ensure_graph()
        total_nodes = left_shape.node_count + right_shape.node_count
        return TypeInfo(TypeTag.GRAPH, GraphShape(total_nodes))

    def _check_connect(self, node: ast.ConnectExpr) -> TypeInfo:
        if not isinstance(node.left, ast.IdentifierExpr):
            raise CheckError("Connect left operand must be an identifier.")
        if not isinstance(node.right, ast.IdentifierExpr):
            raise CheckError("Connect right operand must be an identifier.")

        left_info = self._check_expression(node.left)
        right_info = self._check_expression(node.right)
        left_shape = left_info.ensure_graph()
        right_shape = right_info.ensure_graph()

        self._validate_node_ref(node.left_ref, node.left.name)
        self._validate_node_ref(node.right_ref, node.right.name)

        total_nodes = left_shape.node_count + right_shape.node_count
        return TypeInfo(TypeTag.GRAPH, GraphShape(total_nodes))

    def _check_relabel(self, node: ast.RelabelExpr) -> TypeInfo:
        target_info = self._check_expression(node.target)
        shape = target_info.ensure_graph()
        mapping = node.mapping
        for source, target in mapping.items():
            if source < 0 or source >= shape.node_count:
                raise CheckError(f"Relabel source {source} outside valid range.")
            if target < 0 or target >= shape.node_count:
                raise CheckError(f"Relabel target {target} outside valid range.")
        if len(set(mapping.values())) != len(mapping.values()):
            raise CheckError("Relabel mapping must be injective.")
        return TypeInfo(TypeTag.GRAPH, shape)

    def _check_pick(self, node: ast.PickExpr) -> TypeInfo:
        target_info = self._check_expression(node.target)
        shape = target_info.ensure_graph()
        degree = node.criteria.degree
        if degree < 0:
            raise CheckError("Degree criteria must be non-negative.")
        if degree > shape.node_count - 1 and shape.node_count > 0:
            raise CheckError("Degree criteria exceeds possible node degree.")
        return TypeInfo(TypeTag.NODESET)

    def _check_require(self, node: ast.RequireExpr) -> TypeInfo:
        condition = self._check_expression(node.target)
        if condition.tag != TypeTag.BOOL:
            raise CheckError("Require expects a boolean expression.")
        return TypeInfo(TypeTag.BOOL)

    def _validate_node_ref(self, node_ref: ast.NodeRefLiteral, expected_graph_name: str) -> None:
        if node_ref.graph_name != expected_graph_name:
            raise CheckError(
                f"Node reference {node_ref.graph_name}.{node_ref.index} does not match expected graph '{expected_graph_name}'."
            )
        info = self._env.get(node_ref.graph_name)
        if info is None or info.tag != TypeTag.GRAPH or info.graph is None:
            raise CheckError(
                f"Node reference {node_ref.graph_name}.{node_ref.index} refers to unknown graph."
            )
        if node_ref.index < 0 or node_ref.index >= info.graph.node_count:
            raise CheckError(
                f"Node reference {node_ref.graph_name}.{node_ref.index} outside valid range."
            )

    def _evaluate_motif(self, kind: ast.MotifKind, size: int):
        if kind is ast.MotifKind.RING:
            return ring(size)
        if kind is ast.MotifKind.PATH:
            return path(size)
        if kind is ast.MotifKind.STAR:
            return star(size)
        if kind is ast.MotifKind.MESH:
            return mesh(size)
        raise CheckError(f"Unknown motif kind {kind}.")


def check_program(program: ast.Program) -> CheckResult:
    checker = Checker()
    return checker.check(program)

