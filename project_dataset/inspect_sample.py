import os
import random
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# Directory containing the generated matrices and metadata.
OUT_DIR = "matrices_v1"


def load_meta():
    """
    Load the metadata list from OUT_DIR/meta.npy.

    Returns
    -------
    metas : list[dict]
        List of metadata dictionaries, one per sample.
    """
    meta_path = os.path.join(OUT_DIR, "meta.npy")
    metas = np.load(meta_path, allow_pickle=True)
    return list(metas)


def inspect_one_sample(index=None):
    """
    Visualize a single sample from the generated dataset.

    If `index` is None, a random sample index is chosen. The function:
    - loads the corresponding adjacency matrix
    - converts it to a NetworkX graph
    - prints metadata and matrix shape
    - draws the graph using a fixed spring layout seed for reproducibility

    Parameters
    ----------
    index : int or None
        Index of the sample to inspect. If None, choose a random index.
    """
    metas = load_meta()
    num_samples = len(metas)

    # If no index is specified, pick a random one.
    if index is None:
        index = random.randint(0, num_samples - 1)

    meta = metas[index]
    matrix_path = os.path.join(OUT_DIR, f"graph_{index:05d}.npy")
    A = np.load(matrix_path)

    print(f"Inspecting sample #{index}")
    print("meta:", meta)
    print("matrix shape:", A.shape)

    G = nx.from_numpy_array(A)

    # Plot the graph.
    plt.figure(figsize=(4, 4))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True)
    plt.title(f"Sample #{index} - {meta['type']}")
    plt.show()


if __name__ == "__main__":
    # You can also call inspect_one_sample(0) to inspect a specific index.
    inspect_one_sample()
