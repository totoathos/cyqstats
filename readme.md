# Cyquant

**Cyquant** es una librería para calcular **métricas y percentiles en streaming** (sin comerte la RAM) con un núcleo acelerado en **Cython**. Ideal para logs/CSV/eventos donde Python empieza a toser con los bucles.  

> Objetivo: *agregaciones + p90/p95 por grupo* rápido, reproducible y fácil de integrar con el ecosistema Python.

---

## Features

- **Streaming aggregations**: `count`, `sum`, `mean`, `min`, `max`, `var/std` (según config)
- **Percentiles en streaming**: P² (rápido) y/o **t-digest** (más preciso) *(según implementación)*
- **Group-by eficiente**: por claves pre-encodeadas a `int32` (recomendado) o strings (más lento)
- **Mergeable**: combinar resultados parciales (útil para procesamiento por chunks o paralelo)
- **API simple**: alimentás eventos, pedís resultados
- Núcleo en **Cython + NumPy** (memoryviews, structs, `nogil` donde aplique)

---

## Instalación

### Desde PyPI (cuando publiques)
```bash
pip install streamstats
