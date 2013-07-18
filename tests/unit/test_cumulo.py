import unittest
from cumulus.exceptions import UnconfiguredError
from cumulus.cumulo import CumuloStack

class TestCumulo(unittest.TestCase):

    def test_setregion(self):
        cs = CumuloStack(name='test_case')
        cs.region = 'us-east-1'

        self.assertEqual(cs.region, 'us-east-1')

    def test_set_invalid_region(self):
        cs = CumuloStack(name='test_case')

        self.assertRaises(AttributeError, cs.region, 'a-galaxy-far-away')

    def test_add_arn(self):
        cs = CumuloStack(name='test_case')
        cs.region = 'us-east-1'

        arn = "arn:aws:sns:us-east-1:123456789012:cf_events"
        cs.add_sns_topic(arn=arn)

    def test_add_arn_no_region(self):
        cs = CumuloStack(name='test_case')

        arn = "arn:aws:sns:sa-east-1:123456789012:cf_events"
        self.assertRaises(UnconfiguredError, cs.add_sns_topic, arn=arn)

    def test_add_arn_different_region(self):
        cs = CumuloStack(name='test_case')
        cs.region = 'us-east-1'

        arn = "arn:aws:sns:sa-east-1:123456789012:cf_events"
        self.assertRaises(ValueError, cs.add_sns_topic, arn=arn)
