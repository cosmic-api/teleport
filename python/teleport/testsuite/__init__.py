from unittest2 import defaultTestLoader, TestSuite

def suite():
    import legacy_full_test, legacy_test, draft00_test
    main = defaultTestLoader.loadTestsFromModule(legacy_full_test)
    language = legacy_test.suite()
    draft00 = draft00_test.suite()
    return TestSuite([main, language, draft00])

