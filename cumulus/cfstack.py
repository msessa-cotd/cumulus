import logging
import json
import requests

from .exceptions import TemplateError, ParameterError
from .misc import parse_sns_arn, is_region_supported

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class CFStack(object):

    def __init__(self, name, region, json_template, cf_name=None):
        """
        Instantiate a new CFStack object.
        A CFStack is an actual representation of CloudFormation stack that will be managed.
        For this reason it requires an existing JSON template.

        :param name: Identifier for the stack
        :type name: str
        :param json_template: A path to a local JSON file or a valid S3 URL
        :type json_template: str
        :param cf_name: Override the stack id on cloudformation. Default is the same as the name parameter
        :type cf_name: str
        :return: A CFStack object
        :rtype: cumulus.cfstack.CFStack
        """
        self.name = name
        if is_region_supported(region):
            self.region = region
        else:
            raise AttributeError("Specified region '%s' is not supported" % region)
        self.json_template = json_template
        self.stack_obj = None
        self.dependencies = list()
        self.template_dict = dict()
        if cf_name:
            self.cf_name = cf_name
        else:
            self.cf_name = name

        # Initialise private objects
        self._sns_topics = list()
        self._parameters = dict()
        self._resources = list()
        self._outputs = list()

        if self.json_template.startswith(('http://s3', 'https://s3')):
            log.info("JSON template is hosted externally")
            self._external_template = True
            log.info("Retrieving template data from %s" % self.json_template)
            self.template_content = self._get_template_url()
        else:
            log.info("JSON template is a local file at %s", self.json_template)
            self._external_template = False
            self.template_content = self._get_template_file()

        # Analyse the template
        self.analyse_template()

    def _get_template_file(self):
        with open(self.json_template, 'r') as tpl_file:
            return tpl_file.read()

    def _get_template_url(self):
        http_req = requests.get(self.json_template)
        return http_req.content

    def add_sns_topic(self, arn):
        """
        Add a global SNS topic to the cumulo stack.
        Global SNS topics will be automatically assigned to sub-stacks unless locally overridden
        The region attribute needs to be set before an SNS ARN is added

        :param arn: The full ARN of the SNS topic
        :type arn: str
        :raise ValueError: If the specified ARN is invalid or in a different AWS region
        """

        arn_attrs = parse_sns_arn(arn)

        region = arn_attrs.get('region')
        if region != self.region:
            raise ValueError("SNS topic '%s' is not in the %s region ", arn, self.region)

        self._sns_topics.append(arn)

    def analyse_template(self):
        log.info("Analysing template data")
        self.template_dict = json.loads(self.template_content)
        n_params = 0
        n_resources = 0
        n_outputs = 0
        try:
            log.debug("Analysing parameters")
            tpl_params = self.template_dict['Parameters']
            for param in tpl_params:
                log.debug("Added new parameter: %s", param)
                self._parameters[param] = None
                n_params += 1
        except KeyError:
            # This stack has no parameters, this is accepted
            pass

        try:
            log.debug("Analysing resources")
            tpl_resources = self.template_dict['Resources']
            if not len(tpl_resources):
                raise KeyError
            for res in tpl_resources:
                log.debug("Added new resource: %s", res)
                self._resources.append(res)
                n_resources += 1
        except KeyError:
            raise TemplateError("Template doesn't define any resource")

        try:
            log.debug("Analysing outputs")
            tpl_outputs = self.template_dict['Outputs']
            for out in tpl_outputs:
                log.debug("Added new output: %s", out)
                self._outputs.append(out)
                n_outputs += 1
        except KeyError:
            # This stack has no outputs, this is accepted
            pass
        log.info("Offline analysis complete: Stack %s contains: %d parameter(s), %d resource(s) and %d output(s)"
                 % (self.name, n_params, n_resources, n_outputs))

    class StaticParam(object):
        def __init__(self, p_value):
            self.value = p_value

    class DynamicParam(object):
        def __init__(self, p_type, p_source, p_ref):
            self.type = p_type
            self.source = p_source
            self.ref = p_ref

        @property
        def type(self):
            return self.type

        @type.setter
        def type(self, value):
            if value not in ('resource', 'parameter', 'output'):
                raise ValueError("type attribute must be one of resource, parameter or output")

    def _set_parameter(self, name, param):
        try:
            if self._parameters[name] is None:
                self._parameters[name] = param
            else:
                raise ParameterError("Parameter '%s' for stack '%s' is already set" % (name, self.name))
        except KeyError:
            raise ParameterError("Cannot set unknown parameter '%s' for stack '%s'" % (name, self.name))

    def set_parameter_static(self, name, value):
        sp = self.StaticParam(value)
        self._set_parameter(name, sp)

    def set_parameter_dynamic(self, name, param_type, source, ref):
        dp = self.DynamicParam(param_type, source, ref)
        self._set_parameter(name, dp)

    def get_parameters(self):
        return list(self._parameters.copy().keys())

    def get_unset_parameters(self):
        ret_list = list()
        for param, value in self._parameters.iteritems():
            if value is None:
                ret_list.append(param)
        return ret_list

    def validate_template(self):
        """
        This method will perform validation of the JSON template.
        If the CFStack object was initialised without the online_validation option,
        validation will be performed using the AWS API. Otherwise local code will be used
        :return:
        :rtype:
        """
        pass
        #if self._online_validation

    def add_dependency(self, parent):
        """
        Track a dependency for the substack

        :param parent: Name of another node this substack depends on
        :type parent: str
        """
        self.dependencies.append(parent)