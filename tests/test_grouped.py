from random import Random

from cyquant import GroupedStreamStats


def _mean(values):
    return sum(values) / len(values)


def _var(values):
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / len(values)


def test_grouped_stats_result_arrays():
    rng = Random(7)
    n = 2000
    n_groups = 8
    gids = [rng.randrange(0, n_groups) for _ in range(n)]
    values = [rng.gauss(0, 1) for _ in range(n)]

    g = GroupedStreamStats(n_groups=n_groups)
    g.add(gids, values)
    res = g.result_arrays()

    for gid in range(n_groups):
        group_values = [v for gg, v in zip(gids, values) if gg == gid]
        assert res["count"][gid] == len(group_values)
        if group_values:
            assert abs(res["mean"][gid] - _mean(group_values)) < 1e-9
            assert abs(res["var"][gid] - _var(group_values)) < 1e-9


def test_grouped_merge():
    rng = Random(8)
    n = 500
    n_groups = 5
    gids = [rng.randrange(0, n_groups) for _ in range(n)]
    values = [rng.gauss(0, 1) for _ in range(n)]

    left = GroupedStreamStats(n_groups=n_groups)
    right = GroupedStreamStats(n_groups=n_groups)
    left.add(gids[:250], values[:250])
    right.add(gids[250:], values[250:])
    left.merge(right)

    out = left.to_dict()
    for gid in range(n_groups):
        count = sum(1 for g in gids if g == gid)
        assert out[gid]["count"] == count
