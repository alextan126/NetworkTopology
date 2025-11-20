"""Public API surface for the network topology DSL."""

from .ast import Program
from .checker import CheckError, CheckResult, Checker
from .evaluator import EvaluationError, EvaluationResult, Evaluator, evaluate_program
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
from .parser import ParserError, parse_program
from .types import Graph, NodeId, NodeRef, NodeSet

__all__ = [
    "Graph",
    "NodeId",
    "NodeRef",
    "NodeSet",
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
    "ParserError",
    "parse_program",
    "Checker",
    "CheckResult",
    "CheckError",
    "Evaluator",
    "EvaluationResult",
    "EvaluationError",
    "evaluate_program",
    "Program",
]

