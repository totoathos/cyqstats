from __future__ import annotations

from dataclasses import dataclass
from math import inf, sqrt
from typing import Iterable


@dataclass(slots=True)
class _RunningMoments:
    count: int = 0
    total: float = 0.0
    mean: float = 0.0
    m2: float = 0.0
    minimum: float = inf
    maximum: float = -inf

    def add(self, x: float) -> None:
        x = float(x)
        self.count += 1
        self.total += x
        if x < self.minimum:
            self.minimum = x
        if x > self.maximum:
            self.maximum = x

        delta = x - self.mean
        self.mean += delta / self.count
        delta2 = x - self.mean
        self.m2 += delta * delta2

    def merge(self, other: "_RunningMoments") -> None:
        if other.count == 0:
            return
        if self.count == 0:
            self.count = other.count
            self.total = other.total
            self.mean = other.mean
            self.m2 = other.m2
            self.minimum = other.minimum
            self.maximum = other.maximum
            return

        n1 = self.count
        n2 = other.count
        delta = other.mean - self.mean
        combined_count = n1 + n2

        self.mean = (n1 * self.mean + n2 * other.mean) / combined_count
        self.m2 = self.m2 + other.m2 + delta * delta * n1 * n2 / combined_count
        self.count = combined_count
        self.total += other.total
        self.minimum = min(self.minimum, other.minimum)
        self.maximum = max(self.maximum, other.maximum)


class StreamStats:
    """Streaming stats container for numeric values."""

    def __init__(self) -> None:
        self._agg = _RunningMoments()

    def add_values(self, values: Iterable[float]) -> None:
        for x in values:
            self._agg.add(x)

    def merge(self, other: "StreamStats") -> None:
        if not isinstance(other, StreamStats):
            raise TypeError("other must be StreamStats")
        self._agg.merge(other._agg)

    def result(self) -> dict[str, float | int | None]:
        count = self._agg.count
        if count == 0:
            return {
                "count": 0,
                "sum": 0.0,
                "mean": None,
                "min": None,
                "max": None,
                "var": None,
                "std": None,
            }

        variance = max(self._agg.m2 / count, 0.0)
        return {
            "count": count,
            "sum": self._agg.total,
            "mean": self._agg.mean,
            "min": self._agg.minimum,
            "max": self._agg.maximum,
            "var": variance,
            "std": sqrt(variance),
        }
