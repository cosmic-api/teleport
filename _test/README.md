Common Test Suite
-----------------

There are many tests, but they all work the same way: for a given JSON schema
they provide JSON values that are expected to be of that type and values that
are expected not to be. For each language one must write a simple plugin to
use this test suite. Try running:

    python test_python.py
