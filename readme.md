# Cyqstats

**Cyqstats** es una librería para cálculo de métricas en streaming orientada a datasets grandes.

## Estado actual (MVP)

Este repositorio ya incluye la base funcional para avanzar:

- `StreamStats` para agregaciones incrementales globales:
  - `count`, `sum`, `mean`, `min`, `max`, `var`, `std`.
- `GroupedStreamStats` para agregaciones por grupo (`int32` recomendado en tu pipeline):
  - `add(group_ids, values)`, `merge(...)`, `to_dict()`, `result_arrays()`.
- Merge estable por fórmula de momentos (Welford combinable), ideal para procesar por chunks.

## Quickstart

```python
from random import Random
from cyqstats import StreamStats, GroupedStreamStats

rng = Random(42)
values = [rng.gauss(0, 1) for _ in range(100_000)]

# Global
s = StreamStats()
s.add_values(values)
print(s.result())

# Grouped
gids = [i % 50 for i in range(len(values))]
g = GroupedStreamStats(n_groups=50)
g.add(gids, values)
print(g.result_arrays()["mean"][:5])
```

## Instalación local

```bash
pip install -U pip
pip install -e ".[dev]"
```

## Tests

```bash
PYTHONPATH=src pytest -q
```

## Próximos pasos recomendados

1. **Cythonizar el hot path** (`add_values` y `add`) manteniendo esta API.
2. Agregar percentiles streaming (P² como primera implementación).
3. Añadir benchmark CLI comparando contra `pandas.groupby`.
4. Publicar wheels (`manylinux`, `macOS`, `Windows`).

## Licencia

MIT.
