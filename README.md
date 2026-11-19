# Mini-Courier Planner (ETCCDA302 Capstone)

Python prototype that takes parcels + a road network and produces (1) a priority-sorted parcel list,
(2) an optimal packing plan for one trip (0/1 knapsack DP) and (3) an ordered delivery route
(Dijkstra + nearest-neighbour TSP approximation, refined with 2-opt).

## Files
| File | Purpose |
|---|---|
| `algorithms.py` | Merge/Quick/Insertion sort, knapsack DP (+greedy), Dijkstra, NN-TSP, 2-opt, brute-force TSP |
| `planner.py` | Integrated pipeline + trip report |
| `data_gen.py` | Seeded dataset generator -> `data/{small,medium,large}/parcels.csv, graph.csv` |
| `benchmark.py` | Phase 4 experiments -> `charts/*.png`, `benchmark_results.json` |
| `tests/test_algorithms.py` | 11 unit tests (correctness vs brute force / Bellman-Ford / `sorted`) |
| `REPORT.md` / `REPORT.docx` | Final report |

## Run (Python 3.8+, only `matplotlib` needed for charts)
```
python data_gen.py                    # (re)create datasets
python planner.py data/small 30       # dataset folder, van capacity in kg
python planner.py data/medium 150
python planner.py data/large 600
python -m unittest discover -s tests -v
python benchmark.py                   # regenerates charts/
```
Dataset format: `parcels.csv` = parcel_id,dest,weight,priority,deadline_hr ; `graph.csv` = u,v,distance_km (undirected, node 0 = depot).
