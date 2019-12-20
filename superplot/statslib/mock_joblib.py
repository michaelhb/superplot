"""
Trivial implementation of joblib's Memory class, used as a mock for
Sphinx documentation.
"""

class MockMemory(object):
    def cache(self, func, *args, **kwargs):
        return func

memory = MockMemory()
