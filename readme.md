# Cyqstats

**Cyqstats** es una librería de Python para calcular estadísticas en tiempo real (count/sum/mean/min/max/var/std) sobre grandes volúmenes de datos sin cargar todo en memoria. Incluye agregaciones por grupo (IDs enteros) y permite mergear acumuladores, ideal para pipelines por chunks o procesamiento paralelo. Tiene core en Cython para mejor rendimiento y se instala directo con pip.

## Estado actual (MVP)

Este repositorio ya incluye la base funcional para avanzar:

- `StreamStats` para agregaciones incrementales globales:
  - `count`, `sum`, `mean`, `min`, `max`, `var`, `std`.
- `GroupedStreamStats` para agregaciones por grupo (`int32` recomendado en tu pipeline):
  - `add(group_ids, values)`, `merge(...)`, `to_dict()`, `result_arrays()`.
- Merge estable por fórmula de momentos (Welford combinable), ideal para procesar por chunks.
- Wheels publicadas en PyPI (instalación directa con `pip install cyqstats`).

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

## Instalación
```bash
pip install cyqstats
```
Verificar si se esta usando el core Cython
```bash
python -c "from cyqstats import StreamStats; print(StreamStats.__module__)"
```
Esperado:
cyqstats._cycore → core Cython activo ✅
cyqstats.core → fallback Python ✅

## Instalación Local
```bash
pip install -U pip
pip install -e ".[dev]"
```
En Windows, para compilar el core Cython localmente se requiere Microsoft Visual C++ Build Tools.
Si no lo tenés, igual podés desarrollar usando el fallback Python.

## Test
```bash
python -m pytest -q
```

## Próximos pasos:
- Añadir benchmark CLI comparando contra pandas.groupby y numpy (casos: global + grouped).
- Agregar cuantiles aproximados (p50/p90/p99) vía t-digest o P² para telemetría real.
- Exponer API “numpy-friendly” (aceptar np.ndarray directamente y tipos int32/float64 como fast-path).
- Documentar casos de uso (telemetría/ETL) con ejemplos reproducibles.
