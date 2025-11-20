"""Runtime evaluation for the network topology DSL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Union

from . import ast
from .checker import CheckError, Checker
from .motifs import (
    DegreeCriteria,
    connect,
    mesh,
    overlay,
    path,
    pick,
    relabel,
    require,
    ring,
    star,
)
from .types import Graph, NodeSet

RuntimeValue = Union[Graph, NodeSet, bool]

__all__ = ["EvaluationError", "EvaluationResult", "Evaluator", "evaluate_program"]


class EvaluationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    final: Optional[RuntimeValue]
    environment: Dict[str, Graph]


class Evaluator:
    def __init__(self, checker: Checker | None = None) -> None:
        self._checker = checker or Checker()
        self._env: Dict[str, Graph] = {}

    def evaluate(self, program: ast.Program) -> EvaluationResult:
        try:
            self._checker.check(program)
        except CheckError as error:
            raise EvaluationError(str(error)) from error

        self._env.clear()
        for statement in program.statements:
            value = self._eval_expression(statement.expression)
            if not isinstance(value, Graph):
                raise EvaluationError(
                    f"Let binding '{statement.name}' must produce a Graph value."
                )
            self._env[statement.name] = value
        final_value: Optional[RuntimeValue] = None
        if program.expression is not None:
            final_value = self._eval_expression(program.expression)
        return EvaluationResult(final_value, dict(self._env))

    def _eval_expression(self, node: ast.Expression) -> RuntimeValue:
        if isinstance(node, ast.MotifExpr):
            return self._eval_motif(node)
        if isinstance(node, ast.IdentifierExpr):
            return self._eval_identifier(node)
        if isinstance(node, ast.OverlayExpr):
            return self._eval_overlay(node)
        if isinstance(node, ast.ConnectExpr):
            return self._eval_connect(node)
        if isinstance(node, ast.RelabelExpr):
            return self._eval_relabel(node)
        if isinstance(node, ast.PickExpr):
            return self._eval_pick(node)
        if isinstance(node, ast.RequireExpr):
            return self._eval_require(node)
        raise EvaluationError(f"Unsupported expression node: {type(node).__name__}")

    def _eval_motif(self, node: ast.MotifExpr) -> Graph:
        kind = node.kind
        size = node.size
        if kind is ast.MotifKind.RING:
            return ring(size)
        if kind is ast.MotifKind.PATH:
            return path(size)
        if kind is ast.MotifKind.STAR:
            return star(size)
        if kind is ast.MotifKind.MESH:
            return mesh(size)
        raise EvaluationError(f"Unknown motif kind {kind}.")

    def _eval_identifier(self, node: ast.IdentifierExpr) -> Graph:
        graph = self._env.get(node.name)
        if graph is None:
            raise EvaluationError(f"Unknown graph identifier '{node.name}'.")
        return graph

    def _eval_overlay(self, node: ast.OverlayExpr) -> Graph:
        left = self._expect_graph(self._eval_expression(node.left))
        right = self._expect_graph(self._eval_expression(node.right))
        return overlay(left, right)

    def _eval_connect(self, node: ast.ConnectExpr) -> Graph:
        if not isinstance(node.left, ast.IdentifierExpr):
            raise EvaluationError("Connect left operand must be an identifier.")
        if not isinstance(node.right, ast.IdentifierExpr):
            raise EvaluationError("Connect right operand must be an identifier.")

        left_graph = self._eval_identifier(node.left)
        right_graph = self._eval_identifier(node.right)

        left_index = self._resolve_node_ref(node.left_ref, node.left.name)
        right_index = self._resolve_node_ref(node.right_ref, node.right.name)

        return connect(left_graph, right_graph, bridge=(left_index, right_index))

    def _eval_relabel(self, node: ast.RelabelExpr) -> Graph:
        target = self._expect_graph(self._eval_expression(node.target))
        return relabel(target, node.mapping)

    def _eval_pick(self, node: ast.PickExpr) -> NodeSet:
        target = self._expect_graph(self._eval_expression(node.target))
        criteria = DegreeCriteria(node.criteria.degree)
        return pick(target, criteria)

    def _eval_require(self, node: ast.RequireExpr) -> bool:
        condition = self._eval_expression(node.target)
        if not isinstance(condition, bool):
            raise EvaluationError("Require expects a boolean expression.")
        return require(condition)

    def _resolve_node_ref(self, node_ref: ast.NodeRefLiteral, expected: str) -> int:
        if node_ref.graph_name != expected:
            raise EvaluationError(
                f"Node reference {node_ref.graph_name}.{node_ref.index} does not match graph '{expected}'."
            )
        graph = self._env.get(node_ref.graph_name)
        if graph is None:
            raise EvaluationError(
                f"Node reference {node_ref.graph_name}.{node_ref.index} refers to unknown graph."
            )
        if node_ref.index < 0 or node_ref.index >= graph.node_count:
            raise EvaluationError(
                f"Node reference {node_ref.graph_name}.{node_ref.index} outside valid range."
            )
        return node_ref.index

    def _expect_graph(self, value: RuntimeValue) -> Graph:
        if not isinstance(value, Graph):
            raise EvaluationError("Expected a graph value.")
        return value


def evaluate_program(program: ast.Program) -> EvaluationResult:
    evaluator = Evaluator()
    return evaluator.evaluate(program)

