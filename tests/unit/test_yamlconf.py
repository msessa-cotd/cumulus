import unittest
import mock
import io
from cumulus.cumulo import CumuloStack
from cumulus.exceptions import ConfigurationError, ParameterError
from cumulus.configparsers import YamlConfigParser

from cumulus.configparsers.yamlconfig import (ERRMSG_MULTIPLEROOTS, ERRMSG_DEPFRMUNKNOWN, ERRMSG_INCORRECTTYPE, ERRMSG_MISSDIRECTIVE)

MINIMAL_YAML_CONF = u"""
example-cumulo:
    region: us-west-2
    stacks:
        substack1:
            cf_template: /path/to/substack1
        substack2:
            cf_template: /path/to/substack2
            depends:
                - substack1
        substack2:
            cf_template: /path/to/substack3
            depends:
                - substack2
            params:
                StaticParam:
                    value: 0.0.0.0/0
                DynamicParam:
                    source   : substack2
                    type     : resource
                    variable : SomeVariable
"""


class TestCumulo(unittest.TestCase):

    def test_loadconfig(self):
        with mock.patch('__builtin__.open', return_value=io.StringIO(MINIMAL_YAML_CONF)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')

    def test_config_with_multiple_roots(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-2
            stacks:
                substack1:
                    cf_template: /path/to/template
        rootstack2:
            region: us-west-1
            stacks:
                substack1:
                    cf_template: /path/to/template
        """

        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        expected_error = ERRMSG_MULTIPLEROOTS % (2)
        self.assertRaisesRegexp(ConfigurationError, expected_error, yc.get_configured_obj)

    def test_config_with_no_region(self):
        TEST_YAML = u"""
        rootstack1:
            stacks:
                substack1:
                    cf_template: /path/to/template
        """

        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        expencted_error = ERRMSG_MISSDIRECTIVE % ('region', 'rootstack1')
        self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)

    def test_config_with_invalid_region_type(self):
        TEST_YAML = u"""
        rootstack1:
            region:
                - I shouldn't be a list
            stacks:
                substack1:
                    cf_template: /path/to/template
        """

        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        expencted_error = ERRMSG_INCORRECTTYPE % ('region', 'rootstack1', 'str')
        self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)

    def test_config_with_no_stacks(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-1
        """

        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        expencted_error = ERRMSG_MISSDIRECTIVE % ('stacks', 'rootstack1')
        self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)

    def test_config_with_invalid_stacks_type(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-1
            stacks: I should be a dict
        """

        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        expencted_error = ERRMSG_INCORRECTTYPE % ('stacks', 'rootstack1', 'dict')
        self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)

    def test_config_with_invalid_sns_type(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-1
            sns-topic-arn: I should be a list
            stacks:
                substack1:
                    cf_template: /path/to/template
        """

        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        expencted_error = ERRMSG_INCORRECTTYPE % ('sns-topic-arn', 'rootstack1', 'list')
        self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)

    def test_config_with_invalid_disable_rollback_type(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-1
            disable-rollback: I should be a bool
            stacks:
                substack1:
                    cf_template: /path/to/template
        """
        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        expencted_error = ERRMSG_INCORRECTTYPE % ('disable-rollback', 'rootstack1', 'bool')
        self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)

    def test_config_with_invalid_cf_template_type(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-1
            stacks:
                substack1:
                    cf_template:
                        - I shouldn't be a list
        """
        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        expencted_error = ERRMSG_INCORRECTTYPE % ('cf_template', 'substack1', 'str')
        self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)

    def test_config_with_invalid_depends_type(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-1
            stacks:
                substack1:
                    cf_template: /path/to/template
                    depends: I should be a list
        """
        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        with mock.patch('cumulus.cfstack.CFStack._get_template_file', return_value='{}'):
            with mock.patch('cumulus.cfstack.CFStack.analyse_template'):
                expencted_error = ERRMSG_INCORRECTTYPE % ('depends', 'substack1', 'list')
                self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)


    def test_config_with_unknown_depends(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-1
            stacks:
                substack1:
                    cf_template: /path/to/template
                    depends:
                        - substack2
        """
        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        with mock.patch('cumulus.cfstack.CFStack._get_template_file',  return_value='{}'):
            with mock.patch('cumulus.cfstack.CFStack.analyse_template'):
                expencted_error = ERRMSG_DEPFRMUNKNOWN % ('substack2', 'substack1')
                self.assertRaisesRegexp(ConfigurationError, expencted_error, yc.get_configured_obj)

    def test_config_with_unknown_param(self):
        TEST_YAML = u"""
        rootstack1:
            region: us-west-1
            stacks:
                substack1:
                    cf_template: /path/to/template
                    params:
                        Param1:
                            value: test
                        Param2:
                            value: case
        """
        with mock.patch('__builtin__.open', return_value=io.StringIO(TEST_YAML)):
            yc = YamlConfigParser(yamlfile='/path/to/yamlfile')
        with mock.patch('cumulus.cfstack.CFStack._get_template_file',  return_value='{}'):
            with mock.patch('cumulus.cfstack.CFStack.analyse_template'):
                self.assertRaises(ParameterError, yc.get_configured_obj)