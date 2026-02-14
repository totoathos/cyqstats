from __future__ import annotations

from itertools import zip_longest
from math import nan, sqrt
from typing import Iterable
from importlib import import_module
from .core import _RunningMoments

try:
    _GroupedImpl = import_module("cyqstats._cycore").CyGroupedStreamStats
except Exception:
    _GroupedImpl = None


class PyGroupedStreamStats:
    """Streaming stats partitioned by int group ids (pure Python fallback)."""

    def __init__(self, n_groups: int) -> None:
        if n_groups <= 0:
            raise ValueError("n_groups must be > 0")
        self.n_groups = int(n_groups)
        self._aggs = [_RunningMoments() for _ in range(self.n_groups)]

    def add(self, group_ids: Iterable[int], values: Iterable[float]) -> None:
        marker = object()
        for gid, value in zip_longest(group_ids, values, fillvalue=marker):
            if gid is marker or value is marker:
                raise ValueError("group_ids and values must have the same length")
            idx = int(gid)
            if idx < 0 or idx >= self.n_groups:
                raise ValueError(f"group id {idx} out of range [0, {self.n_groups})")
            self._aggs[idx].add(value)

    def merge(self, other: "PyGroupedStreamStats") -> None:
        if not isinstance(other, PyGroupedStreamStats):
            raise TypeError("other must be PyGroupedStreamStats")
        if other.n_groups != self.n_groups:
            raise ValueError("n_groups mismatch")
        for left, right in zip(self._aggs, other._aggs):
            left.merge(right)

    def to_dict(self) -> dict[int, dict[str, float | int | None]]:
        out: dict[int, dict[str, float | int | None]] = {}
        for i, agg in enumerate(self._aggs):
            if agg.count == 0:
                out[i] = {"count": 0, "sum": 0.0, "mean": None, "min": None, "max": None, "var": None, "std": None}
                continue
            variance = max(agg.m2 / agg.count, 0.0)
            out[i] = {
                "count": agg.count,
                "sum": agg.total,
                "mean": agg.mean,
                "min": agg.minimum,
                "max": agg.maximum,
                "var": variance,
                "std": sqrt(variance),
            }
        return out

    def result_arrays(self) -> dict[str, list[float | int]]:
        counts = [a.count for a in self._aggs]
        sums = [a.total for a in self._aggs]
        means = [a.mean if a.count else nan for a in self._aggs]
        mins = [a.minimum if a.count else nan for a in self._aggs]
        maxs = [a.maximum if a.count else nan for a in self._aggs]
        vars_ = [max(a.m2 / a.count, 0.0) if a.count else nan for a in self._aggs]
        stds = [sqrt(v) if v == v else nan for v in vars_]  # v==v => no es NaN
        return {"count": counts, "sum": sums, "mean": means, "min": mins, "max": maxs, "var": vars_, "std": stds}


# Export público: Cython si está, si no fallback Python
GroupedStreamStats = _GroupedImpl or PyGroupedStreamStats  # type: ignore

__all__ = ["GroupedStreamStats", "PyGroupedStreamStats"]
