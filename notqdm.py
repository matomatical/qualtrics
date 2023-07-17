"""
mock tqdm with the features I use, so that it can be an optional dependency
"""

import sys

class tqdm:
    def __init__(self, *args, **kwargs):
        if args:
            self.iterable = args[0]
        else:
            self.iterable = None
    
    def __iter__(self):
        print("[qualtrics.py] install tqdm for live progress bar here", file=sys.stderr)
        return iter(self.iterable)

    def update(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        print(*args, **kwargs)
