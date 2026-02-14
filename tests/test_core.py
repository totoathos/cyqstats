from random import Random

from cyqstats import StreamStats
from cyqstats.core import PyStreamStats



def _mean(values):
    return sum(values) / len(values)


def _var(values):
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / len(values)


def test_streamstats_matches_reference():
    rng = Random(42)
    values = [rng.gauss(0, 1) for _ in range(1000)]

    s = StreamStats()
    s.add_values(values)
    r = s.result()

    assert r["count"] == len(values)
    assert abs(r["sum"] - sum(values)) < 1e-9
    assert abs(r["mean"] - _mean(values)) < 1e-9
    assert abs(r["min"] - min(values)) < 1e-12
    assert abs(r["max"] - max(values)) < 1e-12
    assert abs(r["var"] - _var(values)) < 1e-9


def test_streamstats_merge():
    rng = Random(10)
    values = [rng.gauss(0, 1) for _ in range(2000)]

    a = StreamStats()
    b = StreamStats()
    a.add_values(values[:1000])
    b.add_values(values[1000:])
    a.merge(b)

    merged = a.result()
    assert merged["count"] == 2000
    assert abs(merged["mean"] - _mean(values)) < 1e-9
    assert abs(merged["var"] - _var(values)) < 1e-9


def test_variance_is_clamped_to_zero_for_numerical_noise():
    s = PyStreamStats()
    s.add_values([1.0])
    s._agg.m2 = -1e-15

    out = s.result()
    assert out["var"] == 0.0
    assert out["std"] == 0.0
