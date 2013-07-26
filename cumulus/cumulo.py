import contextlib
import logging
import boto
import boto.cloudformation

import hashlib

from .graph import StackDependencyGraph
from .misc import parse_sns_arn, is_region_supported
from .cfstack import CFStack

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class CumuloStack(object):
    """
    Main class to orchestrate provisioning. Holds an index of substacks and a connection to AWS.
    """

    def __init__(self, name, region):
        self.name = name
        if is_region_supported(region):
            self.region = region
        else:
            raise AttributeError("Specified region '%s' is not supported" % region)

        # Initialise private properties

        self._cf_connection = None
        self._substacks = dict()
        self._dep_graph = StackDependencyGraph()

    def __repr__(self):
        return "CumuloStack(%s)" % self.name


    def add_substack(self, cfstack):
        log.info("Adding substack %s", cfstack.name)

        self._substacks[cfstack.name] = cfstack

        log.debug("Adding stack %s to dependency graph", cfstack.name)
        self._dep_graph.add_node(cfstack.name)
        for dep in cfstack.dependencies:
            self._dep_graph.add_dependency(dep, cfstack.name)

    def _connect_cf(self):
        """
        Return a saved CloudFormationConnection object or initialise one

        :return: A CloudFormation connection object
        :rtype: CloudFormationConnection
        """
        if not self._cf_connection:
            log.info("Connecting to CloudFormation on region %s", self.region)
            self._cf_connection = boto.cloudformation.connect_to_region(self.region)
        return self._cf_connection

    def list_substacks(self):
        return list(self._substacks.copy().keys())

    def get_substack(self, name):
        return self._substacks[name]

    def get_substacks_status(self, stack_name=None):
        ret_dict = dict()
        log.debug("Describing all stacks")
        cf_stacks = {st.stack_name : st for st in self._connect_cf().describe_stacks()}
        for stack_id, stack_obj in self._substacks.iteritems():
            stack_status = dict()
            if stack_obj.cf_name in cf_stacks:
                log.debug("Retrieving template for stack %s", stack_id)

                #stack_status['running_template_md5'] = running_template_md5
                #stack_status['local_template_md5'] = local_template_md5
            ret_dict[stack_id] = stack_status
        return ret_dict

    def _get_status(self, stack_obj):
        stack_status = dict()
        local_md5, remote_md5 = self._compare_templates(stack_obj)


    def _compare_templates(self, stack_obj):
        """
        Retrieve the local template MD5 and the runinng template MD5
        :param stack_name: The ID of the substack
        :type stack_name: str
        :return: A tuple of form (local_md5, running_md5). running_md5 might be None if the stack is not online
        :rtype: tuple
        """
        stack_running_template = self._connect_cf().get_template(stack_obj.cf_name)
        running_template_md5 = hashlib.md5().update(stack_running_template).digest()
        local_template_md5 = hashlib.md5().update(stack_obj.template_content).digest()
        print running_template_md5
        print local_template_md5
        return local_template_md5, running_template_md5







