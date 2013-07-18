import sys
import argparse


def cli_main(argv=None):

    DESCRIPTION = 'Cumulus helps you manage your CloudFormation stacks'
    LOG_LEVELS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

    conf_parser = argparse.ArgumentParser(description=DESCRIPTION)
    conf_parser.add_argument("-y", "--yamlfile", dest="yamlfile",
                             required=True, type=argparse.FileType('r'),
                             help="Existing YAML file with a Cumulo stack definition")
    conf_parser.add_argument("-l", "--log", dest="loglevel", metavar='LEVEL',
                             required=False, choices=LOG_LEVELS, default="INFO",
                             help="Log Level for output messages. Choices are %s" % ','.join(LOG_LEVELS))
    conf_parser.add_argument("-L", "--botolog", dest="botologlevel", metavar='LEVEL',
                             required=False, choices=LOG_LEVELS, default="CRITICAL",
                             help="Log Level for boto messages. Choices are %s" % ','.join(LOG_LEVELS))

    subparsers = conf_parser.add_subparsers(help='Available commands')

    parser_status = subparsers.add_parser('status', help='Print a status summary of the configured stacks')
    parser_status.add_argument("-s", "--stack", dest="stackname", required=False, help="Select a specific stack")

    parser_create = subparsers.add_parser('create', help='Create stacks on CloudFormation')
    parser_create.add_argument("-s", "--stack", dest="stackname", required=False, help="Select a specific stack")
    parser_create.add_argument("-l", "--linear", dest="linear", required=False, default=False,
                               action='store_true', help="Create one stack at a time")

    parser_update = subparsers.add_parser('update', help='Update stacks on CloudFormation')
    parser_update.add_argument("-s", "--stack", dest="stackname", required=False, help="Select a specific stack")

    parser_delete = subparsers.add_parser('delete', help='Delete stacks on CloudFormation')
    parser_delete.add_argument("-s", "--stack", dest="stackname", required=False, help="Select a specific stack")

    args = conf_parser.parse_args(args=argv)
