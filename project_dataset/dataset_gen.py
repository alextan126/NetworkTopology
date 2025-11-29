import os
import random
import numpy as np
import networkx as nx


# Output directory for the generated adjacency matrices and metadata.
OUT_DIR = "matrices_v1"
os.makedirs(OUT_DIR, exist_ok=True)


def gen_ring_sample():
    """
    Generate a ring graph sample.

    The function creates an undirected cycle graph with a random number of nodes
    and returns its adjacency matrix along with basic metadata.

    Returns
    -------
    A : np.ndarray
        Adjacency matrix of shape (n, n) with 0/1 entries.
    meta : dict
        Dictionary with fields:
        - "type": str, always "ring"
        - "n": int, number of nodes in the ring
    """
    n = random.randint(5, 12)
    G = nx.cycle_graph(n)
    A = nx.to_numpy_array(G, dtype=np.float32)
    meta = {
        "type": "ring",
        "n": n,
    }
    return A, meta


def gen_star_sample():
    """
    Generate a star graph sample.

    We use networkx.star_graph(k), which creates a star with:
    - node 0 as the center
    - nodes 1..k as leaves

    Returns
    -------
    A : np.ndarray
        Adjacency matrix of shape (k+1, k+1).
    meta : dict
        Dictionary with fields:
        - "type": str, always "star"
        - "num_leaves": int, number of leaves
        - "center": int, index of the center node (always 0)
    """
    k = random.randint(4, 12)
    G = nx.star_graph(k)
    A = nx.to_numpy_array(G, dtype=np.float32)
    meta = {
        "type": "star",
        "num_leaves": k,
        "center": 0,
    }
    return A, meta


def gen_grid_sample():
    """
    Generate a 2D grid graph sample.

    We first create a grid_2d_graph(rows, cols) whose nodes are (i, j) pairs,
    then relabel them to a contiguous integer range [0, N-1] to match the
    conventions used in the rest of the project.

    Returns
    -------
    A : np.ndarray
        Adjacency matrix of shape (rows * cols, rows * cols).
    meta : dict
        Dictionary with fields:
        - "type": str, always "grid"
        - "rows": int, number of grid rows
        - "cols": int, number of grid columns
    """
    rows = random.randint(2, 4)
    cols = random.randint(2, 4)
    G = nx.grid_2d_graph(rows, cols)

    # Nodes are (i, j) pairs; map them to {0, ..., N-1}.
    mapping = {node: idx for idx, node in enumerate(G.nodes())}
    G = nx.relabel_nodes(G, mapping)

    A = nx.to_numpy_array(G, dtype=np.float32)
    meta = {
        "type": "grid",
        "rows": rows,
        "cols": cols,
    }
    return A, meta


def gen_tree_sample():
    """
    Generate a balanced tree graph sample.

    We use networkx.balanced_tree(r, h), which creates a rooted tree where
    each internal node has r children and the tree has height h.

    Returns
    -------
    A : np.ndarray
        Adjacency matrix of shape (n, n), where n depends on (r, h).
    meta : dict
        Dictionary with fields:
        - "type": str, always "tree"
        - "r": int, branching factor
        - "h": int, tree height
    """
    r = random.randint(2, 3)
    h = random.randint(2, 4)
    G = nx.balanced_tree(r, h)
    A = nx.to_numpy_array(G, dtype=np.float32)
    meta = {
        "type": "tree",
        "r": r,
        "h": h,
    }
    return A, meta


def gen_two_rings_connect_sample():
    """
    Generate a graph consisting of two rings connected by a single bridge edge.

    This creates two disjoint cycle graphs (with sizes n1 and n2), relabels
    the second one to avoid node index collisions, composes them into a single
    graph, and then adds one random "bridge" edge between a node in the first
    ring and a node in the second ring.

    Returns
    -------
    A : np.ndarray
        Adjacency matrix of shape (n1 + n2, n1 + n2).
    meta : dict
        Dictionary with fields:
        - "type": str, always "two_rings_connect"
        - "n1": int, size of the first ring
        - "n2": int, size of the second ring
        - "bridge": (int, int), the endpoints of the bridge edge in the
          final relabeled node index space
    """
    n1 = random.randint(4, 8)
    n2 = random.randint(4, 8)

    G1 = nx.cycle_graph(n1)
    G2 = nx.cycle_graph(n2)

    # Relabel the second ring so that its node indices follow after the first.
    offset = max(G1.nodes()) + 1
    G2 = nx.relabel_nodes(G2, lambda x: x + offset)

    G = nx.compose(G1, G2)

    # Sample a random bridge between the two rings.
    u = random.choice(list(G1.nodes()))
    v = random.choice(list(G2.nodes()))
    G.add_edge(u, v)

    A = nx.to_numpy_array(G, dtype=np.float32)
    meta = {
        "type": "two_rings_connect",
        "n1": n1,
        "n2": n2,
        "bridge": (int(u), int(v)),
    }
    return A, meta


def sample_one_graph():
    """
    Sample a single graph instance from a mixture of topology generators.

    This function randomly chooses one of the topology generators defined
    above (ring, star, grid, tree, two-rings-connected) and returns the
    corresponding adjacency matrix and metadata.

    Returns
    -------
    A : np.ndarray
        Adjacency matrix of the sampled graph.
    meta : dict
        Metadata describing the sampled graph.
    """
    generators = [
        gen_ring_sample,
        gen_star_sample,
        gen_grid_sample,
        gen_tree_sample,
        gen_two_rings_connect_sample,
    ]
    gen_fn = random.choice(generators)
    return gen_fn()


def main():
    """
    Generate a dataset of adjacency matrices for structured graph topologies.

    For each sample, we:
    - sample a graph using `sample_one_graph()`
    - save its adjacency matrix as `graph_{index:05d}.npy`
    - record its metadata (including index and matrix shape) in a list

    At the end, we save the full metadata list as `meta.npy` in OUT_DIR.
    """
    metas = []

    # Total number of samples to generate.
    num_samples = 50000

    for i in range(num_samples):
        A, meta = sample_one_graph()

        # Save adjacency matrix.
        matrix_path = os.path.join(OUT_DIR, f"graph_{i:05d}.npy")
        np.save(matrix_path, A)

        # Attach index and shape to metadata.
        meta["index"] = i
        meta["shape"] = A.shape
        metas.append(meta)

        print(f"[{i}] saved matrix to {matrix_path}, meta = {meta}")

    # Save all metadata as a single NumPy file.
    meta_path = os.path.join(OUT_DIR, "meta.npy")
    np.save(meta_path, metas, allow_pickle=True)
    print("All meta saved to", meta_path)


if __name__ == "__main__":
    main()
