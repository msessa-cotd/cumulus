import contextlib
import logging
import boto
import boto.cloudformation

from .graph import StackDependencyGraph
from .misc import parse_sns_arn, is_region_supported

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


    def list_substacks(self):
        return list(self._substacks.copy().keys())

    def get_substack(self, name):
        return self._substacks[name]

