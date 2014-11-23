from unittest2 import defaultTestLoader, TestSuite

def suite():
    import draft00_test
    draft00 = defaultTestLoader.loadTestsFromModule(draft00_test)
    return TestSuite([draft00])

