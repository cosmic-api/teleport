from unittest2 import defaultTestLoader, TestSuite

def suite():
    import teleport_test, language_test
    main = defaultTestLoader.loadTestsFromModule(teleport_test)
    language = language_test.suite()
    return TestSuite([main, language])

