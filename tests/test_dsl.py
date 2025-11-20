from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from networkdsl import (
    DegreeCriteria,
    EvaluationError,
    Graph,
    NodeSet,
    connect,
    evaluate_program,
    overlay,
    parse_program,
    path,
    pick,
    relabel,
    ring,
)
from networkdsl.cli import main as cli_main


def test_ring_motif_edges() -> None:
    graph = ring(4)
    assert graph.node_count == 4
    assert set(graph.edges) == {(0, 1), (1, 2), (2, 3), (0, 3)}


def test_overlay_disjoint_union() -> None:
    combined = overlay(ring(3), path(3))
    assert combined.node_count == 6
    # Edges from the original motifs remain
    assert (0, 1) in combined.edges
    assert (3, 4) in combined.edges
    # Overlay does not add cross edges
    assert (0, 3) not in combined.edges


def test_connect_adds_bridge() -> None:
    graph = connect(ring(3), path(3), bridge=(0, 0))
    assert graph.node_count == 6
    assert (0, 3) in graph.edges


def test_pick_degree_one_nodes() -> None:
    graph = path(5)
    nodes = pick(graph, DegreeCriteria(1))
    assert isinstance(nodes, NodeSet)
    assert nodes.nodes == frozenset({0, 4})


def test_relabel_permutation() -> None:
    graph = path(3)
    remapped = relabel(graph, {0: 1, 1: 2, 2: 0})
    assert remapped.node_count == 3
    assert (0, 2) in remapped.edges
    assert (1, 2) in remapped.edges


def test_parse_and_evaluate_program() -> None:
    source = """
let R1 = Ring(4)
let R2 = Ring(6)
let G = Connect(R1, R2, bridge=(R1.1, R2.3))
G
"""
    program = parse_program(source)
    result = evaluate_program(program)
    assert isinstance(result.final, Graph)
    assert result.final.node_count == 10
    assert (1, 7) in result.final.edges


def test_invalid_node_reference_raises() -> None:
    source = """
let R = Ring(4)
let S = Ring(4)
Connect(R, S, bridge=(R.4, S.0))
"""
    program = parse_program(source)
    with pytest.raises(EvaluationError):
        evaluate_program(program)


def test_cli_outputs_graph(tmp_path, capsys) -> None:
    source = "let R = Ring(3)\nR\n"
    program_path = tmp_path / "program.dsl"
    program_path.write_text(source, encoding="utf-8")

    exit_code = cli_main([str(program_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Graph(nodes=3" in captured.out

