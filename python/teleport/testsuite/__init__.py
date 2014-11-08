from unittest2 import defaultTestLoader, TestSuite

def suite():
    import legacy_full_test, legacy_test
    main = defaultTestLoader.loadTestsFromModule(legacy_full_test)
    language = legacy_test.suite()
    return TestSuite([main, language])

