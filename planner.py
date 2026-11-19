"""
Mini-Courier Planner - integrated pipeline.
  Phase 2: merge sort parcels (deadline asc, priority desc)  ->  0/1 knapsack DP picks the trip load
  Phase 3: Dijkstra from depot + each stop -> distance matrix -> nearest-neighbour TSP (+2-opt) route
Usage:  python planner.py [dataset_folder] [capacity]
"""
import csv, os, sys, time
from algorithms import (merge_sort, knapsack_dp, dijkstra, build_path,
                        nearest_neighbour_tour, two_opt, tour_length)

DEPOT = 0

def load_parcels(path):
    with open(path) as f:
        return [dict(parcel_id=r["parcel_id"], dest=int(r["dest"]), weight=int(r["weight"]),
                     priority=int(r["priority"]), deadline_hr=int(r["deadline_hr"])) for r in csv.DictReader(f)]

def load_graph(path):
    g = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            u, v, w = int(r["u"]), int(r["v"]), float(r["distance_km"])
            g.setdefault(u, []).append((v, w)); g.setdefault(v, []).append((u, w))   # undirected
    return g

def parcel_value(p):
    """Value used by the knapsack: priority points + urgency bonus for deadlines <= 4h."""
    return p["priority"] * 10 + (20 if p["deadline_hr"] <= 4 else 0)

def plan(parcels, graph, capacity, verbose=False):
    t = {}
    # ---- Phase 2a: prioritise (earliest deadline first, ties -> higher priority first)
    t0 = time.perf_counter()
    ordered = merge_sort(parcels, key=lambda p: (p["deadline_hr"], -p["priority"]))
    t["sorting"] = time.perf_counter() - t0
    # ---- Phase 2b: choose best set for one trip
    t0 = time.perf_counter()
    best_val, idx, _ = knapsack_dp([p["weight"] for p in ordered], [parcel_value(p) for p in ordered], capacity)
    t["knapsack"] = time.perf_counter() - t0
    loaded = [ordered[i] for i in idx]
    deferred = [p for i, p in enumerate(ordered) if i not in set(idx)]
    # ---- Phase 3a: Dijkstra from depot and each distinct delivery node
    stops = sorted({p["dest"] for p in loaded})
    nodes = [DEPOT] + stops
    t0 = time.perf_counter()
    dist, parents = {}, {}
    for s in nodes:
        dist[s], parents[s] = dijkstra(graph, s)
    t["dijkstra"] = time.perf_counter() - t0
    # ---- Phase 3b: TSP approximation
    t0 = time.perf_counter()
    nn_tour, nn_len = nearest_neighbour_tour(dist, DEPOT, nodes)
    t["nearest_neighbour"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    opt_tour, opt_len = two_opt(dist, nn_tour)
    t["two_opt"] = time.perf_counter() - t0
    # expand the stop-to-stop hops into actual road paths
    full = [DEPOT]
    for a, b in zip(opt_tour, opt_tour[1:]):
        full += build_path(parents[a], b)[1:]
    return dict(ordered=ordered, value=best_val, loaded=loaded, deferred=deferred, stops=stops,
                dist=dist, nn_tour=nn_tour, nn_len=nn_len, opt_tour=opt_tour, opt_len=opt_len,
                full_route=full, times=t,
                load_weight=sum(p["weight"] for p in loaded))

def report(res, capacity):
    L = []
    L.append("=" * 64); L.append(" MINI-COURIER PLANNER - TRIP REPORT"); L.append("=" * 64)
    L.append("\n[Phase 2] Parcels sorted by deadline (then priority):")
    L.append(f"  {'ID':<7}{'Dest':>5}{'Wt':>4}{'Prio':>5}{'DL(h)':>6}{'Value':>6}")
    for p in res["ordered"][:15]:
        L.append(f"  {p['parcel_id']:<7}{p['dest']:>5}{p['weight']:>4}{p['priority']:>5}{p['deadline_hr']:>6}{parcel_value(p):>6}")
    if len(res["ordered"]) > 15: L.append(f"  ... ({len(res['ordered']) - 15} more)")
    L.append(f"\n[Phase 2] Knapsack (capacity {capacity} kg): loaded {len(res['loaded'])}/{len(res['ordered'])} parcels,"
             f" weight {res['load_weight']} kg, total value {res['value']}")
    L.append("  Loaded  : " + ", ".join(p["parcel_id"] for p in res["loaded"]))
    L.append("  Deferred: " + (", ".join(p["parcel_id"] for p in res["deferred"][:20]) or "none")
             + (" ..." if len(res["deferred"]) > 20 else ""))
    L.append(f"\n[Phase 3] Delivery stops (graph nodes): {res['stops']}")
    d = res["dist"][DEPOT]
    L.append("  Dijkstra shortest distance depot -> stop: " + ", ".join(f"{s}:{d[s]:g}" for s in res["stops"]))
    L.append("  Nearest-neighbour route : " + " -> ".join(map(str, res["nn_tour"])) + f"   ({res['nn_len']:g} km)")
    L.append("  After 2-opt improvement : " + " -> ".join(map(str, res["opt_tour"])) + f"   ({res['opt_len']:g} km)")
    L.append("  Full road path (final)  : " + " -> ".join(map(str, res["full_route"])))
    L.append("\n[Timing] " + ", ".join(f"{k}={v*1000:.3f} ms" for k, v in res["times"].items()))
    return "\n".join(L)

if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "small")
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    res = plan(load_parcels(os.path.join(folder, "parcels.csv")), load_graph(os.path.join(folder, "graph.csv")), cap)
    print(report(res, cap))
