"""Minimal CLI for executing network topology DSL programs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from .evaluator import EvaluationError, evaluate_program
from .parser import ParserError, parse_program
from .types import Graph, NodeSet


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute a network topology DSL program.")
    parser.add_argument("source", help="Path to the DSL source file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    source_path = Path(args.source)
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"error: unable to read {source_path}: {error}", file=sys.stderr)
        return 1

    try:
        program = parse_program(source_text)
    except ParserError as error:
        print(f"parse error: {error}", file=sys.stderr)
        return 2

    try:
        result = evaluate_program(program)
    except EvaluationError as error:
        print(f"evaluation error: {error}", file=sys.stderr)
        return 3

    final_value = result.final
    if final_value is None:
        print("No result.")
    elif isinstance(final_value, Graph):
        print(_format_graph(final_value))
    elif isinstance(final_value, NodeSet):
        print(_format_nodes(final_value))
    elif isinstance(final_value, bool):
        print("true" if final_value else "false")
    else:
        print(repr(final_value))
    return 0


def _format_graph(graph: Graph) -> str:
    header = f"Graph(nodes={graph.node_count}, edges={len(graph.edges)})"
    edge_lines = [f"{u} -- {v}" for u, v in sorted(graph.edges)]
    return "\n".join([header, *edge_lines]) if edge_lines else header


def _format_nodes(nodes: NodeSet) -> str:
    ordered = ", ".join(str(index) for index in sorted(nodes.nodes))
    return f"NodeSet({{{ordered}}})"


if __name__ == "__main__":
    raise SystemExit(main())

