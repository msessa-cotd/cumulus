import os
import errno
import logging
import json
import requests

from .exceptions import TemplateError

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

class CFStack(object):

    def __init__(self, name, json_template):
        """
        Instantiate a new CFStack object.
        A CFStack is an actual representation of CloudFormation stack that will be managed.
        For this reason it requires an existing JSON template.

        :param name: Identifier for the stack
        :type name: str
        :param json_template: A path to a local JSON file or a valid S3 URL
        :type json_template: str
        :return: A CFStack object
        :rtype: cumulus.cfstack.CFStack
        """
        self.json_template = json_template
        self.stack_obj = None
        self.dependencies = list()

        self._parameters = list()
        self._resources = list()
        self._outputs = list()

        if self.json_template.startswith(('http://s3', 'https://s3')):
            log.info("JSON template is hosted externally")
            self._external_template = True
            log.info("Retrieving template data from %s" % self.json_template)
            http_req = requests.get(self.json_template)
            self.template_content = http_req.content
        else:
            log.info("JSON template is a local file at %s", self.json_template)
            self._external_template = False
            with open(self.json_template, 'r') as tpl_file:
                self.template_content = tpl_file.read()


    def analyse_template(self):
        log.info("Analysing template data")
        self.template_dict = json.loads(self.template_content)

        try:
            log.debug("Analysing parameters")
            tpl_params = self.template_dict['Parameters']
            for param in tpl_params:
                log.debug("Added new parameter: %s", param)
                self._parameters.append(param)
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
        except KeyError:
            raise TemplateError("Template doesn't define any resource")

        try:
            log.debug("Analysing outputs")
            tpl_outputs = self.template_dict['Outputs']
            for out in tpl_outputs:
                log.debug("Added new output: %s", out)
                self._outputs.append(out)
        except KeyError:
            # This stack has no outputs, this is accepted
            pass


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

    def add_static_parameter(self, key, value):
        """
        Store a static value for a stack input parameter

        :param key: The name of the input parameter
        :type key: str
        :param value: The static value to assign
        :type value: str
        """