import unittest
import mock
from cumulus.cumulo import CumuloStack

class TestCumulo(unittest.TestCase):

    def test_setregion(self):
        cs = CumuloStack(name='test_case', region='us-east-1')
        self.assertEqual(cs.region, 'us-east-1')

    def test_set_invalid_region(self):
        self.assertRaises(AttributeError, CumuloStack, name='test_case', region='a-galaxy-far-away')

    def test_add_cfstack(self):
        cs = CumuloStack(name='test_case', region='us-east-1')

        with mock.patch("cumulus.cfstack.CFStack") as mock_cfstack:
            mock_cfstack.name = 'substack'
            mock_cfstack.dependencies = ['dep1', 'dep2']
            cs.add_substack(mock_cfstack)
            self.assertDictContainsSubset({'substack' : mock_cfstack}, cs._substacks)
            self.assertItemsEqual(['substack'], cs.list_substacks())
