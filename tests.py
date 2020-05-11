import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()

    suite = loader.discover("tests", pattern="*.py")

    unittest.TextTestRunner(verbosity=1).run(suite)
