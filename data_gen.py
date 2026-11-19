"""Dataset generation (seeded => reproducible). Writes CSV files in data/."""
import csv, random, os, sys

def make_graph(n_nodes, seed=1, extra_edge_factor=1.5):
    """Connected random road network: a random spanning tree + extra edges. Node 0 = depot."""
    rnd = random.Random(seed)
    edges = {}
    for v in range(1, n_nodes):                       # spanning tree guarantees connectivity
        u = rnd.randrange(0, v)
        edges[(u, v)] = rnd.randint(2, 20)
    for _ in range(int(n_nodes * extra_edge_factor)):
        u, v = rnd.sample(range(n_nodes), 2)
        key = (min(u, v), max(u, v))
        edges.setdefault(key, rnd.randint(2, 20))
    return [(u, v, w) for (u, v), w in sorted(edges.items())]

def make_parcels(n, n_nodes, seed=1):
    rnd = random.Random(seed)
    return [dict(parcel_id=f"P{i+1:04d}", dest=rnd.randrange(1, n_nodes),
                 weight=rnd.randint(1, 15), priority=rnd.randint(1, 10),
                 deadline_hr=rnd.randint(1, 24)) for i in range(n)]

def write_csvs(folder, parcels, edges):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "parcels.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(parcels[0])); w.writeheader(); w.writerows(parcels)
    with open(os.path.join(folder, "graph.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["u", "v", "distance_km"]); w.writerows(edges)

if __name__ == "__main__":
    # small: demo dataset  |  medium / large for testing
    for name, n_par, n_nodes, seed in [("small", 12, 9, 7), ("medium", 60, 30, 11), ("large", 300, 120, 21)]:
        write_csvs(os.path.join("data", name), make_parcels(n_par, n_nodes, seed), make_graph(n_nodes, seed))
        print("wrote", name)
