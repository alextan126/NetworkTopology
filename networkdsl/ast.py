"""Abstract syntax tree definitions for the network topology DSL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Union

from .types import NodeId

__all__ = [
    "SourceLocation",
    "Program",
    "LetStatement",
    "Expression",
    "MotifKind",
    "MotifExpr",
    "IdentifierExpr",
    "OverlayExpr",
    "ConnectExpr",
    "NodeRefLiteral",
    "RelabelExpr",
    "PickExpr",
    "DegreeCriteriaExpr",
    "RequireExpr",
]


@dataclass(frozen=True, slots=True)
class SourceLocation:
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class Program:
    statements: List["LetStatement"]
    expression: Optional["Expression"]


@dataclass(frozen=True, slots=True)
class LetStatement:
    name: str
    expression: "Expression"
    location: SourceLocation


class MotifKind(Enum):
    RING = auto()
    PATH = auto()
    STAR = auto()
    MESH = auto()


@dataclass(frozen=True, slots=True)
class MotifExpr:
    kind: MotifKind
    size: int
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class IdentifierExpr:
    name: str
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class OverlayExpr:
    left: "Expression"
    right: "Expression"
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class NodeRefLiteral:
    graph_name: str
    index: NodeId
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class ConnectExpr:
    left: "Expression"
    right: "Expression"
    left_ref: NodeRefLiteral
    right_ref: NodeRefLiteral
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class RelabelExpr:
    target: "Expression"
    mapping: Dict[NodeId, NodeId]
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class DegreeCriteriaExpr:
    degree: int
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class PickExpr:
    target: "Expression"
    criteria: DegreeCriteriaExpr
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class RequireExpr:
    target: "Expression"
    location: SourceLocation


Expression = Union[
    MotifExpr,
    IdentifierExpr,
    OverlayExpr,
    ConnectExpr,
    RelabelExpr,
    PickExpr,
    RequireExpr,
]

