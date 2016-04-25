import os
from unittest import TestLoader


def suite():
    start_dir = os.path.dirname(__file__)
    return TestLoader().discover(start_dir)
