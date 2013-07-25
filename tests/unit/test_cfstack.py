import unittest
import mock
import io
from cumulus.exceptions import TemplateError
from cumulus.cfstack import CFStack

VALID_JSON_TPL = u"""
{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Description": "IPSEC Static route stack",
  "Parameters": {
    "RouteTableID": {
      "Type": "String",
      "Description": "Destination route table"
    },
    "IPSECGatewayID": {
      "Type": "String",
      "Description": "IPSEC Gateway router"
    },
    "Subnet": {
      "Type": "String",
      "Description": "Subnet to route"
    }
  },
  "Resources": {
    "IPSECStaticRoute" : {
      "Type" : "AWS::EC2::Route",
      "Properties" : {
        "RouteTableId" : { "Ref" : "RouteTableID" },
        "DestinationCidrBlock" : { "Ref" : "Subnet" },
        "GatewayId" : { "Ref" : "IPSECGatewayID" }
      }
    }
  },
  "Outputs" : {
    "aStaticValue" : {
      "Value" : "Something"
    },
    "aReferenceValue" : {
      "Value" : {
        "Ref" : "IPSECStaticRoute"
      }
    }
  }
}
"""


class TestCFStack(unittest.TestCase):


    def test_init_localfile(self):
        with mock.patch("__builtin__.open", return_value=io.StringIO(VALID_JSON_TPL)):
            cfs = CFStack(name='test_case', region='us-west-1', json_template='/a/fake/file')

        self.assertMultiLineEqual(cfs.template_content, VALID_JSON_TPL)

    def test_init_url(self):
        with mock.patch("requests.get") as mock_req:
            mock_resp = mock.Mock()
            mock_resp.content = VALID_JSON_TPL
            mock_req.return_value = mock_resp
            cfs = CFStack(name='test_case', region='us-west-1', json_template='https://s3-ap-southeast-1.amazonaws.com/fake/template.json')

        self.assertMultiLineEqual(cfs.template_content, VALID_JSON_TPL)

    def test_analyse_template(self):
        with mock.patch("__builtin__.open", return_value=io.StringIO(VALID_JSON_TPL)):
            cfs = CFStack(name='test_case', region='us-west-1', json_template='/a/fake/file')

        self.assertItemsEqual(cfs._parameters, ['RouteTableID', 'IPSECGatewayID', 'Subnet'])
        self.assertItemsEqual(cfs._resources, ['IPSECStaticRoute'])
        self.assertItemsEqual(cfs._outputs, ['aStaticValue', 'aReferenceValue'])

    def test_analyse_template_noresources(self):
        EMPY_TEMPLATE = u"""
        {
          "AWSTemplateFormatVersion": "2010-09-09",
          "Description": "An empty template"
        }
        """
        with mock.patch("__builtin__.open", return_value=io.StringIO(EMPY_TEMPLATE)):
            self.assertRaises(TemplateError, CFStack, name='test_case', region='us-west-1', json_template='/a/fake/file')

    def test_add_arn(self):
        with mock.patch("__builtin__.open", return_value=io.StringIO(VALID_JSON_TPL)):
            cfs = CFStack(name='test_case', region='us-west-1', json_template='/a/fake/file')

        arn = "arn:aws:sns:us-west-1:123456789012:cf_events"
        cfs.add_sns_topic(arn=arn)

    def test_add_arn_different_region(self):
        with mock.patch("__builtin__.open", return_value=io.StringIO(VALID_JSON_TPL)):
            cfs = CFStack(name='test_case', region='us-west-1', json_template='/a/fake/file')

        arn = "arn:aws:sns:sa-east-1:123456789012:cf_events"
        self.assertRaises(ValueError, cfs.add_sns_topic, arn=arn)