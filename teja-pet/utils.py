"""Shared utility functions used across modules."""
from collections import OrderedDict


def lerp(a, b, t):
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def mix(c1, c2, t):
    """Mix two RGB colour tuples by factor t (0 = c1, 1 = c2)."""
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def smooth(t):
    """Hermite smoothstep (0-1 clamped)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class LRUCache:
    """Simple least-recently-used cache with a max size."""

    def __init__(self, maxsize=64):
        self._data = OrderedDict()
        self._max = maxsize

    def get(self, key, default=None):
        if key in self._data:
            self._data.move_to_end(key)
            return self._data[key]
        return default

    def put(self, key, value):
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        while len(self._data) > self._max:
            self._data.popitem(last=False)

    def clear(self):
        self._data.clear()
