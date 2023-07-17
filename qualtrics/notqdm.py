"""
No TQDM
=======

Mock `tqdm` with the features I use, so that it can be an optional
dependency.
"""

import sys

class tqdm:
    """
    Mock tqdm object, supporting basic features used by the library.
    """
    def __init__(self, *args, **kwargs):
        """
        Swallows any arguments passed. If an iterable was provided, holds on
        to that so it can be passed back upon iteration.
        """
        if args:
            self.iterable = args[0]
        else:
            self.iterable = None
    
    def __iter__(self):
        """
        Print a warning message and pass through to the provided iterator.

        (I guess it will throw an error if you didn't pass an iterable...?)
        """
        print(
            "[qualtrics.notqdm] install tqdm for live progress bar here",
            file=sys.stderr,
        )
        return iter(self.iterable)

    def update(self, *args, **kwargs):
        """
        Swallow all arguments.
        """
        pass

    @staticmethod
    def write(*args, **kwargs):
        """
        Pass arguments straight through to builtin print.
        """
        print(*args, **kwargs)
