"""Phase 4: runtime experiments -> charts/*.png and results printed as tables."""
import random, time, os, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from algorithms import *
from data_gen import make_graph, make_parcels
from planner import plan, load_parcels, load_graph

os.makedirs("charts", exist_ok=True)
def timeit(f, reps=3):
    best = INF
    for _ in range(reps):
        t = time.perf_counter(); f(); best = min(best, time.perf_counter() - t)
    return best * 1000  # ms
rnd = random.Random(42)
out = {}

# 1. sorting
sizes = [100, 250, 500, 1000, 2000, 4000]
S = {"Merge sort": [], "Quick sort": [], "Insertion sort": [], "Python sorted()": []}
for n in sizes:
    a = [rnd.randint(0, 10**6) for _ in range(n)]
    S["Merge sort"].append(timeit(lambda: merge_sort(a)))
    S["Quick sort"].append(timeit(lambda: quick_sort(a)))
    S["Insertion sort"].append(timeit(lambda: insertion_sort(a), 1))
    S["Python sorted()"].append(timeit(lambda: sorted(a)))
out["sorting"] = dict(sizes=sizes, **S)
plt.figure(figsize=(7, 4.2))
for k, v in S.items(): plt.plot(sizes, v, marker="o", label=k)
plt.xlabel("Number of parcels (n)"); plt.ylabel("Time (ms)"); plt.title("Sorting runtime vs input size")
plt.grid(alpha=.3); plt.legend(); plt.tight_layout(); plt.savefig("charts/sorting_runtime.png", dpi=150); plt.close()

# 2. knapsack n x capacity
ns = [50, 100, 200, 400, 800]
caps = [100, 400]
K = {}
for W in caps:
    K[W] = []
    for n in ns:
        w = [rnd.randint(1, 15) for _ in range(n)]; v = [rnd.randint(10, 120) for _ in range(n)]
        K[W].append(timeit(lambda: knapsack_dp(w, v, W), 2))
out["knapsack"] = dict(n=ns, caps={str(k): v for k, v in K.items()})
# DP vs greedy quality
gap = []
for _ in range(200):
    n = rnd.randint(10, 30); w = [rnd.randint(1, 15) for _ in range(n)]; v = [rnd.randint(10, 120) for _ in range(n)]
    W = sum(w) // 3
    gap.append(knapsack_greedy(w, v, W)[0] / knapsack_dp(w, v, W)[0])
out["greedy_vs_dp_avg_ratio"] = sum(gap) / len(gap); out["greedy_vs_dp_min_ratio"] = min(gap)
out["greedy_suboptimal_cases_of_200"] = sum(1 for g in gap if g < 1 - 1e-9)
plt.figure(figsize=(7, 4.2))
for W, v in K.items(): plt.plot(ns, v, marker="o", label=f"capacity W={W}")
plt.xlabel("Number of parcels (n)"); plt.ylabel("Time (ms)"); plt.title("0/1 Knapsack DP runtime  O(n·W)")
plt.grid(alpha=.3); plt.legend(); plt.tight_layout(); plt.savefig("charts/knapsack_runtime.png", dpi=150); plt.close()

# 3. dijkstra
vs = [100, 250, 500, 1000, 2000, 4000]; D = []
for V in vs:
    e = make_graph(V, seed=V); g = {i: [] for i in range(V)}
    for u, v, w in e: g[u].append((v, w)); g[v].append((u, w))
    D.append(timeit(lambda: dijkstra(g, 0)))
out["dijkstra"] = dict(V=vs, ms=D)
plt.figure(figsize=(7, 4.2)); plt.plot(vs, D, marker="o", color="tab:green")
plt.xlabel("Number of graph nodes (V), E ≈ 2.5V"); plt.ylabel("Time (ms)"); plt.title("Dijkstra (binary heap) single-source runtime")
plt.grid(alpha=.3); plt.tight_layout(); plt.savefig("charts/dijkstra_runtime.png", dpi=150); plt.close()

# 4. TSP: runtime NN vs brute force, and quality
def matrix(k, seed):
    r = random.Random(seed); p = [(r.random() * 100, r.random() * 100) for _ in range(k)]
    return {i: {j: ((p[i][0]-p[j][0])**2 + (p[i][1]-p[j][1])**2) ** .5 for j in range(k)} for i in range(k)}
ks = [5, 6, 7, 8, 9]; bf_t, nn_t, ratios_nn, ratios_2 = [], [], [], []
for k in ks:
    M = matrix(k, k); nodes = list(range(k))
    bf_t.append(timeit(lambda: brute_force_tsp(M, 0, nodes), 1)); nn_t.append(timeit(lambda: nearest_neighbour_tour(M, 0, nodes)))
    rn, r2 = [], []
    for s in range(30):
        M2 = matrix(k, 100 + s); nt, nl = nearest_neighbour_tour(M2, 0, nodes); _, ol = two_opt(M2, nt); _, bl = brute_force_tsp(M2, 0, nodes)
        rn.append(nl / bl); r2.append(ol / bl)
    ratios_nn.append(sum(rn) / len(rn)); ratios_2.append(sum(r2) / len(r2))
out["tsp"] = dict(k=ks, brute_ms=bf_t, nn_ms=nn_t, avg_ratio_nn=ratios_nn, avg_ratio_2opt=ratios_2)
big_k = [10, 25, 50, 100, 200]; big_nn, big_2 = [], []
for k in big_k:
    M = matrix(k, k); nodes = list(range(k)); big_nn.append(timeit(lambda: nearest_neighbour_tour(M, 0, nodes)))
    t, _ = nearest_neighbour_tour(M, 0, nodes); big_2.append(timeit(lambda: two_opt(M, t), 1))
out["tsp_large"] = dict(k=big_k, nn_ms=big_nn, two_opt_ms=big_2)
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
ax[0].semilogy(ks, bf_t, marker="o", label="Brute force O(k!)"); ax[0].semilogy(ks, nn_t, marker="s", label="Nearest neighbour O(k²)")
ax[0].set_xlabel("Delivery stops (k)"); ax[0].set_ylabel("Time (ms, log)"); ax[0].set_title("Exact vs approximate TSP runtime"); ax[0].grid(alpha=.3); ax[0].legend()
ax[1].plot(ks, ratios_nn, marker="o", label="Nearest neighbour"); ax[1].plot(ks, ratios_2, marker="s", label="NN + 2-opt")
ax[1].axhline(1, color="gray", ls="--", lw=1); ax[1].set_xlabel("Delivery stops (k)"); ax[1].set_ylabel("Avg route length ÷ optimal"); ax[1].set_title("Approximation quality (30 random maps each)")
ax[1].grid(alpha=.3); ax[1].legend(); plt.tight_layout(); plt.savefig("charts/tsp_comparison.png", dpi=150); plt.close()

# 5. end-to-end breakdown on small/medium/large
E = {}
for name, cap in (("small", 30), ("medium", 150), ("large", 600)):
    r = plan(load_parcels(f"data/{name}/parcels.csv"), load_graph(f"data/{name}/graph.csv"), cap)
    E[name] = {k: v * 1000 for k, v in r["times"].items()}
    E[name].update(parcels=len(r["ordered"]), loaded=len(r["loaded"]), stops=len(r["stops"]), nn_km=r["nn_len"], opt_km=r["opt_len"], cap=cap)
out["end_to_end"] = E
steps = ["sorting", "knapsack", "dijkstra", "nearest_neighbour", "two_opt"]
fig, ax = plt.subplots(figsize=(8, 4.4)); bottom = [0] * 3
for s in steps:
    vals = [E[n][s] for n in E]; ax.bar(list(E), vals, bottom=bottom, label=s.replace("_", " ")); bottom = [b + v for b, v in zip(bottom, vals)]
ax.set_ylabel("Time (ms)"); ax.set_title("End-to-end runtime breakdown by pipeline step"); ax.legend(); plt.tight_layout(); plt.savefig("charts/pipeline_breakdown.png", dpi=150); plt.close()

json.dump(out, open("benchmark_results.json", "w"), indent=1)
print(json.dumps(out, indent=1))
