import yaml
import logging
from ..cumulo import CumuloStack
from ..cfstack import CFStack
from ..exceptions import ConfigurationError

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Error messages formats
ERRMSG_MULTIPLEROOTS = "Only one root object is expected, found %d"
ERRMSG_MISSDIRECTIVE = "Missing mandatory config directive '%s' in object '%s'"
ERRMSG_INCORRECTTYPE = "Config directive '%s' in object '%s' must be a %s type. Found %s type"
ERRMSG_DEPFRMUNKNOWN = "Dependency '%s' in stack '%s' refers to an unknown node"
ERRMSG_PARAMUNEXPECT = "Parameter '%s' in stack '%s' is unexpected"


class YamlConfigParser(object):
    config_dict = dict()

    def __init__(self, yamlfile):
        log.info("Loading configuration file %s", yamlfile)
        try:
            with open(yamlfile, 'r') as conf_file:
                self.config_dict = yaml.safe_load(conf_file)
        except IOError:
            log.critical("Unable to open config file %s", yamlfile)
            return None

    def get_configured_obj(self):
        # Only one root object is allowed
        if len(self.config_dict) != 1:
            raise ConfigurationError(ERRMSG_MULTIPLEROOTS % len(self.config_dict))

        # TODO: Python 3 will drop iteritems() in favour of items()
        cumulo_name, cumulo_conf = next(self.config_dict.iteritems())

        region = cumulo_conf.get('region')
        self._v_type(region, str, 'region', cumulo_name, 'str')

        substacks = cumulo_conf.get('stacks')
        self._v_type(substacks, dict, 'stacks', cumulo_name, 'dict')

        # Initialise a new CumuloStack object
        cumulo = CumuloStack(name=cumulo_name, region=region)

        global_sns_topics = cumulo_conf.get('sns-topic-arn')
        self._v_type(global_sns_topics, list, 'sns-topic-arn', cumulo_name, 'list', required=False)

        global_disable_rollback = cumulo_conf.get('disable-rollback')
        self._v_type(global_disable_rollback, bool, 'disable-rollback', cumulo_name, 'bool', required=False)

        for stack_id, stack_dict in substacks.iteritems():
            cf_template = stack_dict.get('cf_template')
            self._v_type(cf_template, str, 'cf_template', stack_id, 'str')

            # If the substack name is the same as the cumulo name then don't use a suffix
            if stack_id == cumulo_name:
                cf_name = stack_id
            else:
                cf_name = "%s-%s" % (cumulo_name, stack_id)

            # Initialise a new CFStack object
            cfs = CFStack(name=stack_id, region=region, json_template=cf_template, cf_name=cf_name)

            # Register explicit dependencies
            stack_deps = stack_dict.get('depends')
            self._v_type(stack_deps, list, 'depends', stack_id, 'list', required=False)
            if stack_deps:
                for dep in stack_deps:
                    if dep not in substacks:
                        raise ConfigurationError(ERRMSG_DEPFRMUNKNOWN % (dep, stack_id))
                        # Actual registration
                    cfs.add_dependency(dep)

            # Process parameters
            stack_params = stack_dict.get('params')
            self._v_type(stack_params, dict, 'params', stack_id, 'dict', required=False)
            if stack_params:
                for param_id, param_dict in stack_params.iteritems():
                    log.debug("Registering parameter %s for stack %s", param_id, stack_id)
                    param_value = param_dict.get('value')
                    self._v_type(param_value, str, 'value', "%s/params/%s" % (stack_id, param_id), 'str',
                                 required=False)
                    if param_value:
                        # 'value' attribute is set, this must be a static value
                        cfs.set_parameter_static(param_id, param_value)
                    else:
                        param_source = param_dict.get('source')
                        param_type = param_dict.get('type')
                        param_variable = param_dict.get('variable')
                        self._v_type(param_source, str, 'source', "%s/params/%s" % (stack_id, param_id), 'str')
                        self._v_type(param_type, str, 'type', "%s/params/%s" % (stack_id, param_id), 'str')
                        self._v_type(param_variable, str, 'variable', "%s/params/%s" % (stack_id, param_id), 'str')
                        cfs.set_parameter_dynamic(param_id, param_type, param_source, param_variable)


            # Finally, register the CFStack object with the CumuloStack
            cumulo.add_substack(cfs)

        return cumulo

    @staticmethod
    def _v_type(obj, pyt_type, confname, confsection, strtype, required=True):
        if obj:
            if not isinstance(obj, pyt_type):
                raise ConfigurationError(ERRMSG_INCORRECTTYPE % (confname, confsection, strtype, type(obj)))
        else:
            if required:
                raise ConfigurationError(ERRMSG_MISSDIRECTIVE % (confname, confsection))
