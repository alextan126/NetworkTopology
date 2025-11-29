# Network Topology Dataset Generator

This directory contains scripts for generating a large synthetic dataset of graph topologies using NetworkX.  
The generated dataset will be used for training an ML model that maps matrix representations → graph structures.

---

## Overview

We generate a diverse set of structured graphs using five topology types:

- **Ring**
- **Star**
- **Grid (2D lattice)**
- **Balanced tree**
- **Two rings connected by a single bridge**

Each generated graph is stored as:

- an **adjacency matrix** (NumPy `.npy` file)
- an associated **metadata dictionary** (stored collectively in `meta.npy`)

The dataset is designed to be *variable-sized* — different samples have different numbers of nodes.  
This allows flexible training on general graph structures.  
(If padding is needed later, it can be applied as a separate preprocessing step.)

---

## Directory Structure

matrices_v1/
graph_00000.npy
graph_00001.npy
...
graph_49999.npy
meta.npy
dataset_gen.py
inspect_sample.py
README.md


- `graph_XXXXX.npy` — adjacency matrix for the X-th graph  
- `meta.npy` — list of metadata dictionaries (one per sample)
- `dataset_gen.py` — script to generate the dataset  
- `inspect_sample.py` — script to inspect and visualize individual samples  

---

## Metadata Format

Each entry in `meta.npy` is a Python dictionary including:

```python
{
    "type": "ring" | "star" | "grid" | "tree" | "two_rings_connect",
    # Topology-specific fields:
    "n": int,                        # for rings
    "num_leaves": int,               # for stars
    "rows": int, "cols": int,        # for grids
    "r": int, "h": int,              # for trees
    "n1": int, "n2": int,            # for two-rings
    "bridge": (u, v),                # connection between the two rings
    # Common fields:
    "index": int,                    # sample index
    "shape": (N, N),                 # adjacency matrix shape
}
This makes the dataset self-describing and easy to use for downstream ML or DSL synthesis tasks.

How to Generate the Dataset
Running the script:

bash
复制代码
python dataset_gen.py
This will:

generate 50,000 synthetic graph samples

save adjacency matrices into matrices_v1/

save metadata into matrices_v1/meta.npy

If needed, adjust the dataset size:

python
复制代码
num_samples = 50000
inside dataset_gen.py.

How to Inspect a Sample
Use:

bash
复制代码
python inspect_sample.py
This will:

randomly select one sample from matrices_v1

print its metadata

display the graph using NetworkX's spring layout

You can also inspect a specific index:

python
复制代码
inspect_one_sample(123)
Notes
All graphs are undirected and unweighted.

Adjacency matrices are float32, containing 0/1 entries.

Matrix sizes vary depending on topology parameters (e.g., grid size, tree height).

Padding is not applied in this dataset; it can be added later if required for training.