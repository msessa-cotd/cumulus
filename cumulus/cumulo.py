import contextlib
import logging
import boto
import boto.cloudformation

from .graph import StackDependencyGraph
from .exceptions import UnconfiguredError
from .misc import parse_sns_arn

log = logging.getLogger(__name__).addHandler(logging.NullHandler())


class CumuloStack(object):
    """
    Main class to orchestrate provisioning. Holds an index of substacks and a connection to AWS.
    """

    def __init__(self, name):
        self.name = name

        # Initialise private properties
        self._region = None
        self._sns_topics = list()
        self._cf_connection = None
        self._substacks = dict()
        self._dep_graph = StackDependencyGraph()

    def __repr__(self):
        return "CumuloStack(%s)" % self.name

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, value):
        if self._cf_connection:
            raise AttributeError("AWS region cannot be changed once a connection has been established")

        if not value in [r.name for r in boto.cloudformation.regions()]:
            raise AttributeError("Specified region '%s' is not supported" % value)

        self._region = value

    def add_sns_topic(self, arn):
        """
        Add a global SNS topic to the cumulo stack.
        Global SNS topics will be automatically assigned to sub-stacks unless locally overridden
        The region attribute needs to be set before an SNS ARN is added

        :param arn: The full ARN of the SNS topic
        :type arn: str
        :raise UnconfiguredError: If the region attribute was not previously set
        :raise ValueError: If the specified ARN is invalid or in a different AWS region
        """
        if not self._region:
            raise UnconfiguredError("Please set the region attribute before adding a topic")

        arn_attrs = parse_sns_arn(arn)

        region = arn_attrs.get('region')
        if region != self._region:
            raise ValueError("SNS topic '%s' is not in the %s region ", arn, self.region)

        self._sns_topics.append(arn)


