import numpy as np
from numba import jit
from numpy import ndarray


@jit
def add_array(idx: ndarray, idx_a: ndarray, idx_b: ndarray, a: ndarray, b: ndarray):
    """
    Adds two time series with different indices in an event discrete manner. The state
    of a system stays constant until a new event occurs. The resulting time series index
    is a union of the indices of the input time series.

    Params:
        idx: ndarray, the index of the resulting time series (union of idx_a and idx_b)
        idx_a: ndarray, the index of the first time series
        idx_b: ndarray, the index of the second time series
        a: ndarray, the values of the first time series
        b: ndarray, the values of the second time series

    Returns:
        ndarray, the resulting time series
    """
    i, j, k = 0, 0, 0
    res = np.empty(len(idx))
    len_a, len_b = len(a), len(b)

    if len_a == 0:
        return b

    if len_b == 0:
        return a

    while i < len(idx):
        if j >= len_a:
            while k < len_b:
                res[i] = a[j - 1] + b[k]
                k = k + 1
                i = i + 1
            continue

        elif k >= len_b:
            while j < len_a:
                res[i] = a[j] + b[k - 1]
                j = j + 1
                i = i + 1
            continue

        elif idx_a[j] == idx_b[k]:
            res[i] = a[j] + b[k]
            j = j + 1
            k = k + 1
            i = i + 1

        elif idx_a[j] < idx_b[k]:
            res[i] = a[j] + (b[k - 1] if k > 0 else 0)
            j = j + 1
            i = i + 1

        elif idx_a[j] > idx_b[k]:
            res[i] = b[k] + (a[j - 1] if j > 0 else 0)
            k = k + 1
            i = i + 1
    return res


@jit
def add_2d_array(idx: ndarray, idx_a: ndarray, idx_b: ndarray, a: ndarray, b: ndarray):
    """
    Adds two multi column time series with different indices in an event discrete manner.
    The state of a system stays constant until a new event occurs. The resulting time
    series index is a union of the indices of the input time series.

    Args:
        idx: ndarray, the index of the resulting time series (union of idx_a and idx_b)
        idx_a: ndarray, the index of the first time series
        idx_b: ndarray, the index of the second time series
        a: ndarray, the values of the first time series
        b: ndarray, the values of the second time series

    Returns:
        ndarray, the resulting time series
    """
    assert a.shape[1] == b.shape[1], "The number of columns must be the same"
    cols = a.shape[1]
    i, j, k = 0, 0, 0
    res = np.empty((len(idx), a.shape[1]))
    len_a, len_b = len(a), len(b)

    if len_a == 0:
        return b

    if len_b == 0:
        return a

    while i < len(idx):
        if j >= len_a:
            while k < len_b:
                for col in range(cols):
                    res[i, col] = a[j - 1, col] + b[k, col]
                k = k + 1
                i = i + 1
            continue

        elif k >= len_b:
            while j < len_a:
                for col in range(cols):
                    res[i, col] = a[j, col] + b[k - 1, col]
                j = j + 1
                i = i + 1
            continue

        elif idx_a[j] == idx_b[k]:
            for col in range(cols):
                res[i, col] = a[j, col] + b[k, col]
            j = j + 1
            k = k + 1
            i = i + 1

        elif idx_a[j] < idx_b[k]:
            for col in range(cols):
                res[i, col] = a[j, col] + (b[k - 1, col] if k > 0 else 0)
            j = j + 1
            i = i + 1

        elif idx_a[j] > idx_b[k]:
            for col in range(cols):
                res[i, col] = b[k, col] + (a[j - 1, col] if j > 0 else 0)
            k = k + 1
            i = i + 1
    return res
