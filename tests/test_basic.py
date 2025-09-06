"""
Basic tests for SD-Host
"""

import unittest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBasic(unittest.TestCase):
    """Basic tests to ensure project structure is working"""
    
    def test_imports(self):
        """Test that basic imports work"""
        try:
            import src
            self.assertTrue(hasattr(src, '__version__'))
        except ImportError:
            self.fail("Failed to import src package")
    
    def test_version(self):
        """Test that version is defined"""
        import src
        self.assertIsInstance(src.__version__, str)
        self.assertGreater(len(src.__version__), 0)


if __name__ == '__main__':
    unittest.main()
