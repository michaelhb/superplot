"""
Patch the joblib's caching classes so that cached functions can be
doctested. For this the decorator must return a function with correct
__doc__ attribute.
"""

from joblib import Memory
from tempfile import mkdtemp
from functools import update_wrapper


class PatchedMemory(Memory):
    """
    Patch joblib's Memory class so that it may be doctested.
    """     
    def cache(self, func, *args, **kwargs):
        def cfunc(*fargs, **fkwargs):
            return Memory.cache(self, func, *args, **kwargs).__call__(*fargs, **fkwargs)
        update_wrapper(cfunc, func)
        return cfunc


cachedir = mkdtemp()
memory = PatchedMemory(cachedir=cachedir, verbose=0)


@memory.cache
def test_function():
    """
    >>> test_function() == test_function()
    True
    """
    from random import random
    return random()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
