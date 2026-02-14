from __future__ import annotations

from math import nan, sqrt
from typing import Iterable

from .core import _RunningMoments


class GroupedStreamStats:
    """Streaming stats partitioned by int group ids."""

    def __init__(self, n_groups: int) -> None:
        if n_groups <= 0:
            raise ValueError("n_groups must be > 0")
        self.n_groups = int(n_groups)
        self._aggs = [_RunningMoments() for _ in range(self.n_groups)]

    def add(self, group_ids: Iterable[int], values: Iterable[float]) -> None:
        gids = [int(g) for g in group_ids]
        vals = [float(v) for v in values]
        if len(gids) != len(vals):
            raise ValueError("group_ids and values must have the same length")

        for idx, value in zip(gids, vals):
            if idx < 0 or idx >= self.n_groups:
                raise ValueError(f"group id {idx} out of range [0, {self.n_groups})")
            self._aggs[idx].add(value)

    def merge(self, other: "GroupedStreamStats") -> None:
        if not isinstance(other, GroupedStreamStats):
            raise TypeError("other must be GroupedStreamStats")
        if other.n_groups != self.n_groups:
            raise ValueError("n_groups mismatch")
        for left, right in zip(self._aggs, other._aggs):
            left.merge(right)

    def to_dict(self) -> dict[int, dict[str, float | int | None]]:
        out: dict[int, dict[str, float | int | None]] = {}
        for i, agg in enumerate(self._aggs):
            if agg.count == 0:
                out[i] = {
                    "count": 0,
                    "sum": 0.0,
                    "mean": None,
                    "min": None,
                    "max": None,
                    "var": None,
                    "std": None,
                }
                continue
            variance = agg.m2 / agg.count
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
        vars_ = [a.m2 / a.count if a.count else nan for a in self._aggs]
        stds = [sqrt(v) if v == v else nan for v in vars_]
        return {
            "count": counts,
            "sum": sums,
            "mean": means,
            "min": mins,
            "max": maxs,
            "var": vars_,
            "std": stds,
        }
