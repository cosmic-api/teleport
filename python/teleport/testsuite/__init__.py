from unittest2 import defaultTestLoader, TestSuite

def suite():
    import legacy_full_test
    import draft00_test
    import legacy_test
    main = defaultTestLoader.loadTestsFromModule(legacy_full_test)
    draft00 = defaultTestLoader.loadTestsFromModule(draft00_test)
    language = legacy_test.suite()
    return TestSuite([main, language, draft00])

