import os
from unittest2 import TestLoader


def suite():
    start_dir = os.path.dirname(__file__)
    return TestLoader().discover(start_dir)

