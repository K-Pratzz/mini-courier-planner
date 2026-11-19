import sys, os, random, unittest, itertools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from algorithms import *
from planner import plan, load_parcels, load_graph
from data_gen import make_graph, make_parcels

class TestSorting(unittest.TestCase):
    def test_all_sorts_match_builtin(self):
        rnd = random.Random(0)
        for n in (0, 1, 2, 10, 200):
            a = [rnd.randint(-50, 50) for _ in range(n)]
            for f in (merge_sort, quick_sort, insertion_sort):
                self.assertEqual(f(a), sorted(a), f.__name__)
    def test_merge_sort_stable(self):
        data = [(1, "a"), (0, "b"), (1, "c"), (0, "d")]
        self.assertEqual(merge_sort(data, key=lambda x: x[0]), [(0, "b"), (0, "d"), (1, "a"), (1, "c")])
    def test_sorted_and_reverse_inputs(self):
        a = list(range(500))
        self.assertEqual(quick_sort(a), a); self.assertEqual(quick_sort(a[::-1]), a)

class TestKnapsack(unittest.TestCase):
    def test_textbook(self):
        v, ch, _ = knapsack_dp([1, 3, 4, 5], [1, 4, 5, 7], 7)
        self.assertEqual(v, 9); self.assertEqual(sum([1, 3, 4, 5][i] for i in ch) <= 7, True)
    def test_matches_brute_force(self):
        rnd = random.Random(3)
        for _ in range(50):
            n = rnd.randint(1, 9); w = [rnd.randint(1, 10) for _ in range(n)]; val = [rnd.randint(1, 30) for _ in range(n)]
            cap = rnd.randint(1, 30)
            best = max(sum(val[i] for i in s) for r in range(n + 1) for s in itertools.combinations(range(n), r)
                       if sum(w[i] for i in s) <= cap)
            v, ch, _ = knapsack_dp(w, val, cap)
            self.assertEqual(v, best); self.assertEqual(sum(val[i] for i in ch), v)
            self.assertLessEqual(sum(w[i] for i in ch), cap)
    def test_edge_cases(self):
        self.assertEqual(knapsack_dp([5], [10], 4)[0], 0)
        self.assertEqual(knapsack_dp([], [], 10)[0], 0)
    def test_greedy_can_be_suboptimal(self):
        # ratios: A=1.2 (w10,v12) wins greedy; B+C = 2x(w5? ) -> dp better
        w, v = [10, 6, 6], [12, 7, 7]
        self.assertLess(knapsack_greedy(w, v, 12)[0], knapsack_dp(w, v, 12)[0])

class TestGraph(unittest.TestCase):
    def setUp(self):
        self.g = {0: [(1, 4), (2, 1)], 1: [(0, 4), (2, 2), (3, 5)], 2: [(0, 1), (1, 2), (3, 8)], 3: [(1, 5), (2, 8)], 4: []}
    def test_dijkstra(self):
        d, p = dijkstra(self.g, 0)
        self.assertEqual((d[1], d[2], d[3]), (3, 1, 8))
        self.assertEqual(build_path(p, 3), [0, 2, 1, 3])
        self.assertEqual(d[4], INF)                      # unreachable node
    def test_dijkstra_vs_bellman_ford(self):
        edges = make_graph(25, seed=5)
        g = {i: [] for i in range(25)}
        for u, v, w in edges: g[u].append((v, w)); g[v].append((u, w))
        d, _ = dijkstra(g, 0)
        bf = [INF] * 25; bf[0] = 0
        for _ in range(24):
            for u, v, w in edges:
                bf[u] = min(bf[u], bf[v] + w); bf[v] = min(bf[v], bf[u] + w)
        self.assertEqual([d[i] for i in range(25)], bf)

class TestTSP(unittest.TestCase):
    def _matrix(self, k, seed):
        rnd = random.Random(seed); pts = [(rnd.random() * 100, rnd.random() * 100) for _ in range(k)]
        return {i: {j: ((pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2) ** .5 for j in range(k)} for i in range(k)}
    def test_valid_tour_and_quality(self):
        for seed in range(10):
            D = self._matrix(8, seed); nodes = list(range(8))
            nn, nl = nearest_neighbour_tour(D, 0, nodes)
            self.assertEqual(nn[0], 0); self.assertEqual(nn[-1], 0); self.assertEqual(sorted(nn[:-1]), nodes)
            opt, ol = two_opt(D, nn)
            _, bl = brute_force_tsp(D, 0, nodes)
            self.assertLessEqual(ol, nl + 1e-9); self.assertGreaterEqual(ol, bl - 1e-9)
            self.assertEqual(sorted(opt[:-1]), nodes)

class TestIntegration(unittest.TestCase):
    def test_full_pipeline_on_datasets(self):
        base = os.path.join(os.path.dirname(__file__), "..", "data")
        for name, cap in (("small", 30), ("medium", 100), ("large", 300)):
            res = plan(load_parcels(f"{base}/{name}/parcels.csv"), load_graph(f"{base}/{name}/graph.csv"), cap)
            self.assertLessEqual(res["load_weight"], cap)
            self.assertEqual(res["full_route"][0], 0); self.assertEqual(res["full_route"][-1], 0)
            self.assertTrue(set(res["stops"]) <= set(res["full_route"]))
            self.assertLessEqual(res["opt_len"], res["nn_len"] + 1e-9)
            self.assertEqual(len(res["loaded"]) + len(res["deferred"]), len(res["ordered"]))

if __name__ == "__main__":
    unittest.main(verbosity=2)
