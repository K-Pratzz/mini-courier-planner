"""
Mini-Courier Planner - core algorithms (ETCCDA302 Capstone)
Sorting (Merge Sort + Quick/Insertion for comparison), 0/1 Knapsack DP,
Dijkstra (binary heap), Nearest-Neighbour TSP approximation (+ 2-opt, brute force for checking).
"""
import heapq
import itertools
from typing import Callable, Dict, List, Tuple

INF = float("inf")


# ---------------------------------------------------------------- SORTING ---
def merge_sort(arr: List, key: Callable = lambda x: x) -> List:
    """Stable divide-and-conquer sort. O(n log n) time, O(n) space."""
    if len(arr) <= 1:
        return arr[:]
    mid = len(arr) // 2
    left, right = merge_sort(arr[:mid], key), merge_sort(arr[mid:], key)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):   # <= keeps equal keys in original order (stable)
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:]); out.extend(right[j:])
    return out


def quick_sort(arr: List, key: Callable = lambda x: x) -> List:
    """Quick sort (median-of-three pivot, iterative stack to avoid deep recursion).
    Average O(n log n), worst O(n^2). NOT stable. Used for comparison only."""
    a = arr[:]
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        mid = (lo + hi) // 2
        # median of three -> pivot placed at hi
        if key(a[mid]) < key(a[lo]): a[mid], a[lo] = a[lo], a[mid]
        if key(a[hi]) < key(a[lo]): a[hi], a[lo] = a[lo], a[hi]
        if key(a[mid]) < key(a[hi]): a[mid], a[hi] = a[hi], a[mid]
        pivot = key(a[hi])
        i = lo
        for j in range(lo, hi):
            if key(a[j]) < pivot:
                a[i], a[j] = a[j], a[i]; i += 1
        a[i], a[hi] = a[hi], a[i]
        stack.append((lo, i - 1)); stack.append((i + 1, hi))
    return a


def insertion_sort(arr: List, key: Callable = lambda x: x) -> List:
    """O(n^2) baseline, stable."""
    a = arr[:]
    for i in range(1, len(a)):
        cur, j = a[i], i - 1
        while j >= 0 and key(a[j]) > key(cur):
            a[j + 1] = a[j]; j -= 1
        a[j + 1] = cur
    return a


# --------------------------------------------------------------- KNAPSACK ---
def knapsack_dp(weights: List[int], values: List[int], capacity: int):
    """0/1 Knapsack, bottom-up DP. O(n*W) time and space.
    Returns (best_value, chosen_indices, dp_table)."""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]                      # skip item i
            if w <= c and dp[i - 1][c - w] + v > dp[i][c]:
                dp[i][c] = dp[i - 1][c - w] + v          # take item i
    # backtrack to recover chosen items
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            chosen.append(i - 1); c -= weights[i - 1]
    chosen.reverse()
    return dp[n][capacity], chosen, dp


def knapsack_greedy(weights, values, capacity):
    """Greedy by value/weight ratio - fast but not always optimal (for comparison)."""
    order = sorted(range(len(weights)), key=lambda i: values[i] / weights[i], reverse=True)
    total_v, total_w, chosen = 0, 0, []
    for i in order:
        if total_w + weights[i] <= capacity:
            total_w += weights[i]; total_v += values[i]; chosen.append(i)
    return total_v, sorted(chosen)


# --------------------------------------------------------------- DIJKSTRA ---
Graph = Dict[int, List[Tuple[int, float]]]


def dijkstra(graph: Graph, source: int):
    """Single-source shortest paths with a binary heap. O((V+E) log V).
    Returns (dist, parent)."""
    dist = {v: INF for v in graph}
    parent = {v: None for v in graph}
    dist[source] = 0
    pq = [(0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue                                     # stale entry
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v], parent[v] = nd, u
                heapq.heappush(pq, (nd, v))
    return dist, parent


def build_path(parent: Dict[int, int], target: int) -> List[int]:
    path = []
    while target is not None:
        path.append(target); target = parent[target]
    return path[::-1]


# -------------------------------------------------------------------- TSP ---
def nearest_neighbour_tour(dist: Dict[int, Dict[int, float]], start: int, nodes: List[int]):
    """Greedy TSP approximation: always visit the closest unvisited stop, then return.
    O(k^2) for k stops. Returns (tour incl. return to start, length)."""
    unvisited = set(nodes) - {start}
    tour, cur, total = [start], start, 0.0
    while unvisited:
        nxt = min(unvisited, key=lambda x: dist[cur][x])
        total += dist[cur][nxt]; tour.append(nxt); unvisited.remove(nxt); cur = nxt
    total += dist[cur][start]; tour.append(start)
    return tour, total


def tour_length(dist, tour):
    return sum(dist[a][b] for a, b in zip(tour, tour[1:]))


def two_opt(dist, tour):
    """Optimisation step: repeatedly reverse segments while it shortens the tour. O(k^2) per pass."""
    best = tour[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                a, b, c, d = best[i - 1], best[i], best[j], best[j + 1]
                if dist[a][c] + dist[b][d] < dist[a][b] + dist[c][d] - 1e-12:
                    best[i:j + 1] = reversed(best[i:j + 1]); improved = True
    return best, tour_length(dist, best)


def brute_force_tsp(dist, start, nodes):
    """Exact TSP, O(k!) - only for tiny inputs, used to measure approximation quality."""
    others = [n for n in nodes if n != start]
    best, best_len = None, INF
    for perm in itertools.permutations(others):
        t = [start, *perm, start]
        l = tour_length(dist, t)
        if l < best_len:
            best, best_len = t, l
    return best, best_len
