import contextlib

class Cumulo:
    """
    Main class for cumulus. Holds an index of substacks and orchestrates provisioning
    """
    def __init__(self, name, region='us-east-1'):
        self.name = name
        self.region = region

    @contextlib.contextmanager
    def _get_cf_connection(self):
        if ( not isinstance(self.cfconnection, boto.cloudformation.CloudFormationConnection) ):
            logger.info('Connecting to CloudFormation on region %s' % self.get_instance_region())
            self.cfconnection = boto.cloudformation.connect_to_region(region_name=self.get_instance_region())
        yield self.cfconnection