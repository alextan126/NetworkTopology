# Network Topology DSL – Programming-Language Guide

This note walks through the design of the mini DSL with as little jargon as possible.  
Use it as a map for how the pieces fit together and why each exists.

---

## 1. Big Picture

The system lets us describe small network motifs (ring, path, star, mesh) in a tiny language and then combine them.  
To make that work we split the project into three layers:

1. **Types (`networkdsl/types.py`)** – concrete data structures that represent graphs and node references.
2. **Operations (`networkdsl/motifs.py`, `networkdsl/checker.py`, `networkdsl/evaluator.py`)** – functions that build or analyse those structures.
3. **Language surface (`networkdsl/lexer.py`, `networkdsl/parser.py`)** – code that reads DSL text and turns it into the structures above.

Think of layer 1 as the Lego bricks, layer 2 as the construction rules, and layer 3 as the human-friendly instructions.

---

## 2. Why `types.py` Matters

Even though Python is dynamically typed, we still need a _single_ definition for what a “graph” is so the rest of the system shares the same assumptions.

### 2.1 `Graph`

```text
Graph
├─ node_count : int
└─ edges      : set of (node_id, node_id)
```

- **`node_count`** says how many nodes exist (nodes are numbered `0 … node_count-1`).
- **`edges`** stores undirected connections. When you add an edge `(2, 5)` it automatically normalizes to `(2, 5)` (ordering doesn’t matter) and checks that both endpoints are in range.
- Utility methods (`has_node`, `neighbors`, `degree`, `with_extra_edges`, `relabel`) let other modules work with graphs without duplicating logic.

Having these checks in one place guarantees that all motifs, parsers, and evaluators see a consistent, validated graph.

### 2.2 `NodeRef` and `NodeSet`

- **`NodeRef`** models things like `R1.5` (graph named `R1`, node index `5`).  
  It keeps us from mixing up a raw integer with a reference that also needs a graph name.
- **`NodeSet`** is just a frozen set of node IDs, used when selectors like `Pick` return a collection of nodes.

If we tried to inline these structs in multiple files, we would risk subtle differences (and bugs). Centralizing them is the cheapest way to “enforce types” in Python.

---

## 3. How the DSL Flows

Here’s how a program such as:

```
let R = Ring(4)
let S = Star(4)
Connect(R, S, bridge=(R.1, S.0))
```

moves through the system:

```text
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│ Source Text │ -> │ Lexer Tokens │ -> │ AST (objects │
└─────────────┘    └──────────────┘    │ from ast.py) │
                                        └──────┬───────┘
                                               │
                         ┌─────────────────────┴─────────────────────┐
                         │ Checker (type + validity rules)           │
                         │ - Motif constraints (n ≥ 3, etc.)         │
                         │ - NodeRef range checks                    │
                         └─────────────────────┬─────────────────────┘
                                               │
                                ┌──────────────┴──────────────┐
                                │ Evaluator (builds Graphs)   │
                                │ - Calls motifs/connect/etc. │
                                │ - Returns Graph / NodeSet   │
                                └──────────────┬──────────────┘
                                               │
                                  ┌────────────┴────────────┐
                                  │ Final Graph structure   │
                                  │ (from types.Graph)      │
                                  └─────────────────────────┘
```

Every arrow between boxes carries values defined in `types.py`.

---

## 4. What “Type Enforcement” Means Here

Because we’re in Python, we can’t rely on the compiler to stop bad programs. Instead we:

1. **Validate eagerly:** `Graph` raises errors if edges are out of range or duplicated, `NodeRef` prevents negative indices, and so on.
2. **Check before running:** The `Checker` walks the AST verifying that expressions respect the DSL rules (e.g., you can’t connect two graphs without valid node references).
3. **Reuse the same structures:** The evaluator doesn’t need extra guards because it trusts the checker and the guaranteed invariants in `Graph`.

Centralizing the data model in `types.py` is what makes steps 1 and 2 powerful enough to give us “type safety” in a dynamic language.

---

## 5. Quick Reference

| Concept          | Defined In     | Purpose                                                |
| ---------------- | -------------- | ------------------------------------------------------ |
| `Graph`          | `types.py`     | Immutable base structure for all motifs & compositions |
| `NodeRef`        | `types.py`     | Stores `graph_name` + `node_id` for things like `R1.5` |
| `DegreeCriteria` | `motifs.py`    | Explains what `Pick` matches (`deg=<int>`)             |
| `Program` AST    | `ast.py`       | Object form of the parsed DSL                          |
| `Checker`        | `checker.py`   | Enforces DSL rules before we build actual graphs       |
| `Evaluator`      | `evaluator.py` | Executes the AST into real `Graph`/`NodeSet` results   |
| CLI              | `cli.py`       | Runs `.dsl` files end to end                           |

---

## 6. When You Modify the DSL

If you add new motifs or language constructs, follow the same pattern:

1. Update the tokenizer & parser to understand the syntax.
2. Extend the AST with a new node type if necessary.
3. Teach the checker what constraints the new construct needs.
4. Implement the runtime behaviour in the evaluator (often reusing `Graph` helpers).

Because the data structures are centrally defined, each new feature has a clean target for where its logic lives.

---

That’s the whole story: `types.py` is the glue that keeps the DSL predictable. Everything else layers on top of those definitions to give you readable network topology programs.
