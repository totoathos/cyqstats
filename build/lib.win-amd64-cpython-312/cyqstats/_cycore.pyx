# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
from libc.math cimport sqrt
from libc.float cimport DBL_MAX
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from itertools import zip_longest

import numpy as np
cimport numpy as cnp

cnp.import_array()

ctypedef struct Agg:
    Py_ssize_t count
    double total
    double mean
    double m2
    double minimum
    double maximum

cdef inline void agg_reset(Agg* a) nogil:
    a.count = 0
    a.total = 0.0
    a.mean = 0.0
    a.m2 = 0.0
    a.minimum = DBL_MAX
    a.maximum = -DBL_MAX

cdef inline void agg_add(Agg* a, double x) nogil:
    cdef double delta, delta2
    a.count += 1
    a.total += x
    if x < a.minimum:
        a.minimum = x
    if x > a.maximum:
        a.maximum = x

    delta = x - a.mean
    a.mean += delta / a.count
    delta2 = x - a.mean
    a.m2 += delta * delta2

cdef inline void agg_merge(Agg* a, Agg* b) nogil:
    cdef Py_ssize_t n1, n2, combined
    cdef double delta
    if b.count == 0:
        return
    if a.count == 0:
        a.count = b.count
        a.total = b.total
        a.mean = b.mean
        a.m2 = b.m2
        a.minimum = b.minimum
        a.maximum = b.maximum
        return

    n1 = a.count
    n2 = b.count
    combined = n1 + n2
    delta = b.mean - a.mean

    a.mean = (n1 * a.mean + n2 * b.mean) / combined
    a.m2 = a.m2 + b.m2 + delta * delta * n1 * n2 / combined
    a.count = combined
    a.total += b.total
    if b.minimum < a.minimum:
        a.minimum = b.minimum
    if b.maximum > a.maximum:
        a.maximum = b.maximum


cdef class CyStreamStats:
    cdef Agg _a

    def __cinit__(self):
        agg_reset(&self._a)

    def add_values(self, values):
        """
        Fast path: buffer (numpy/memoryview) float64.
        Fallback: iterable.
        """
        cdef double[:] v
        try:
            v = values
        except TypeError:
            for x in values:
                agg_add(&self._a, float(x))
            return

        cdef Py_ssize_t i, n = v.shape[0]
        with nogil:
            for i in range(n):
                agg_add(&self._a, v[i])

    def merge(self, other):
        if not isinstance(other, CyStreamStats):
            raise TypeError("other must be StreamStats")
        cdef CyStreamStats o = other
        with nogil:
            agg_merge(&self._a, &o._a)

    def result(self):
        cdef Py_ssize_t c = self._a.count
        if c == 0:
            return {
                "count": 0,
                "sum": 0.0,
                "mean": None,
                "min": None,
                "max": None,
                "var": None,
                "std": None,
            }
        cdef double var_ = self._a.m2 / c
        if var_ < 0.0:
            var_ = 0.0
        return {
            "count": int(c),
            "sum": self._a.total,
            "mean": self._a.mean,
            "min": self._a.minimum,
            "max": self._a.maximum,
            "var": var_,
            "std": sqrt(var_),
        }


cdef class CyGroupedStreamStats:
    cdef Py_ssize_t n_groups
    cdef Agg* _aggs

    def __cinit__(self, int n_groups):
        if n_groups <= 0:
            raise ValueError("n_groups must be > 0")
        self.n_groups = n_groups
        self._aggs = <Agg*> PyMem_Malloc(n_groups * sizeof(Agg))
        if self._aggs == NULL:
            raise MemoryError()
        cdef Py_ssize_t i
        for i in range(n_groups):
            agg_reset(&self._aggs[i])

    def __dealloc__(self):
        if self._aggs != NULL:
            PyMem_Free(self._aggs)
            self._aggs = NULL

    def add(self, group_ids, values):
        cdef Py_ssize_t i, n
        cdef Py_ssize_t bad_i = -1
        cdef long bad_gid = 0
        cdef long gid
        cdef Py_ssize_t idx

        cdef Py_ssize_t ng = self.n_groups      # local C
        cdef Agg* aggs = self._aggs             # local C

        cdef double[:] vals
        cdef cnp.int32_t[:] gids32
        cdef cnp.int64_t[:] gids64

        # values: fast-path buffer
        try:
            vals = values
        except TypeError:
            # fallback full python (streaming, sin listas)
            sentinel = object()
            for g, v in zip_longest(group_ids, values, fillvalue=sentinel):
                if g is sentinel or v is sentinel:
                    raise ValueError("group_ids and values must have the same length")
                idx = <Py_ssize_t>int(g)
                if idx < 0 or idx >= ng:
                    raise ValueError(f"group id {idx} out of range [0, {ng})")
                agg_add(&aggs[idx], float(v))
            return

        # group_ids: fast-path int32
        try:
            gids32 = group_ids
            if gids32.shape[0] != vals.shape[0]:
                raise ValueError("group_ids and values must have the same length")

            n = vals.shape[0]
            with nogil:
                for i in range(n):
                    gid = <long>gids32[i]
                    if gid < 0 or gid >= ng:
                        bad_i = i
                        bad_gid = gid
                        break
                    agg_add(&aggs[gid], vals[i])

            if bad_i != -1:
                raise ValueError(f"group id {bad_gid} out of range [0, {ng})")
            return
        except TypeError:
            pass

        # group_ids: fast-path int64
        bad_i = -1
        try:
            gids64 = group_ids
            if gids64.shape[0] != vals.shape[0]:
                raise ValueError("group_ids and values must have the same length")

            n = vals.shape[0]
            with nogil:
                for i in range(n):
                    gid = <long>gids64[i]
                    if gid < 0 or gid >= ng:
                        bad_i = i
                        bad_gid = gid
                        break
                    agg_add(&aggs[gid], vals[i])

            if bad_i != -1:
                raise ValueError(f"group id {bad_gid} out of range [0, {ng})")
            return
        except TypeError:
            pass

        # fallback: group_ids iterable, values buffer (vals)
        sentinel = object()
        for g, v in zip_longest(group_ids, vals, fillvalue=sentinel):
            if g is sentinel or v is sentinel:
                raise ValueError("group_ids and values must have the same length")
            idx = <Py_ssize_t>int(g)
            if idx < 0 or idx >= ng:
                raise ValueError(f"group id {idx} out of range [0, {ng})")
            agg_add(&aggs[idx], float(v))

    def merge(self, other):
        if not isinstance(other, CyGroupedStreamStats):
            raise TypeError("other must be GroupedStreamStats")
        cdef CyGroupedStreamStats o = other
        if o.n_groups != self.n_groups:
            raise ValueError("n_groups mismatch")

        cdef Py_ssize_t i
        cdef Py_ssize_t ng = self.n_groups
        cdef Agg* left = self._aggs
        cdef Agg* right = o._aggs

        with nogil:
            for i in range(ng):
                agg_merge(&left[i], &right[i])

    def to_dict(self):
        out = {}
        cdef Py_ssize_t i
        cdef double var_
        cdef Agg* a
        cdef Py_ssize_t ng = self.n_groups
        cdef Agg* aggs = self._aggs

        for i in range(ng):
            a = &aggs[i]
            if a.count == 0:
                out[i] = {"count": 0, "sum": 0.0, "mean": None, "min": None, "max": None, "var": None, "std": None}
            else:
                var_ = a.m2 / a.count
                if var_ < 0.0:
                    var_ = 0.0
                out[i] = {
                    "count": int(a.count),
                    "sum": a.total,
                    "mean": a.mean,
                    "min": a.minimum,
                    "max": a.maximum,
                    "var": var_,
                    "std": float(sqrt(var_)),
                }
        return out

    def result_arrays(self):
        nan = float("nan")
        cdef Py_ssize_t ng = self.n_groups
        cdef Agg* aggs = self._aggs

        counts = [0] * ng
        sums = [0.0] * ng
        means = [nan] * ng
        mins = [nan] * ng
        maxs = [nan] * ng
        vars_ = [nan] * ng
        stds = [nan] * ng

        cdef Py_ssize_t i
        cdef double var_
        cdef Agg* a

        for i in range(ng):
            a = &aggs[i]
            if a.count == 0:
                continue
            counts[i] = int(a.count)
            sums[i] = a.total
            means[i] = a.mean
            mins[i] = a.minimum
            maxs[i] = a.maximum
            var_ = a.m2 / a.count
            if var_ < 0.0:
                var_ = 0.0
            vars_[i] = var_
            stds[i] = float(sqrt(var_))

        return {"count": counts, "sum": sums, "mean": means, "min": mins, "max": maxs, "var": vars_, "std": stds}