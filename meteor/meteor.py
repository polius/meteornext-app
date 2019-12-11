# -*- coding: utf-8 -*-
import os
import sys
import json
import uuid
import traceback
import logging
import argparse
import time

import deploy
from colors import colored

# Execute Meteor using $ python meteor.py ...
if __name__ == '__main__':
    from meteor import meteor
    meteor() 

class meteor:
    def __init__(self):
        self._logger = self.__init_logger_stream()
        self._args = self.__init_parser()

        # Set the Default Logs Path (if it has not been set by the user)
        if self._args.logs_path is None:
            self._args.uuid = uuid.uuid4()
            self._args.logs_path = '{}/logs/{}'.format(os.path.dirname(os.path.realpath(__file__)), self._args.uuid)
        else:
            self._args.logs_path = self._args.logs_path[:-1] if self._args.logs_path.endswith('/') else self._args.logs_path

        # Start Meteor Execution
        self.start()

    def start(self):
        try: 
            # Load the Core
            core = deploy.deploy(self._logger, self._args)

            # Remote Execution - Check SSH Connection
            core.check_remote_execution()
            
            # Init Core
            core.init()

        except KeyboardInterrupt:
            self._logger.warning("")
            self._logger.warning(colored("+==================================================================+", 'yellow'))
            self._logger.warning(colored("|  WARNING                                                         |", 'yellow'))
            self._logger.warning(colored("+==================================================================+", 'yellow'))
            self._logger.warning("Program Interrupted By User.")
            core.clean()

        except Exception as e:
            self.__print_error()
            message = str(e).replace('[USER] ', '') if str(e).startswith('[USER] ') else str(e)
            print(colored("Message: ", attrs=['bold']) + message)
            # if not str(e).startswith('[USER] '):
            #     self._logger.critical(colored("Showing Error Traceback ...", attrs=['bold']))
            #     self._logger.critical(traceback.format_exc())
            core.clean()

    ####################
    # Internal Methods #
    ####################
    def __print_error(self):
        print(colored("+==================================================================+", 'red', attrs=['bold']))
        print(colored("|  ERROR                                                           |", 'red', attrs=['bold']))
        print(colored("+==================================================================+", 'red', attrs=['bold']))

    def __init_logger_stream(self):
        try:
            # Create Logger
            logger = logging.getLogger('meteor')
            logger.setLevel(logging.DEBUG)

            # Create Stream Handler
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console_format = logging.Formatter('%(message)s')
            console.setFormatter(console_format)
            logger.addHandler(console)

            # Return Logger
            return logger

        except Exception:
            print("Cannot init the Logger module.")
            sys.exit()

    def __init_parser(self):
        try:
            parser = argparse.ArgumentParser(description='meteor')
            # User Commands
            ## Core Commands
            parser.add_argument('--environment', required=False, action='store', dest='environment', help=argparse.SUPPRESS)
            parser.add_argument('--servers', required=False, action='store', dest='servers', help=argparse.SUPPRESS)
            parser.add_argument('--validate', required=False, action='store', dest='validate', help=argparse.SUPPRESS)
            parser.add_argument('--test', required=False, action='store_true', dest='test', help=argparse.SUPPRESS)
            parser.add_argument('--deploy', required=False, action='store_true', dest='deploy', help=argparse.SUPPRESS)

            ## Additional Commands
            parser.add_argument('--logs_path', required=False, action='store', dest='logs_path', help=argparse.SUPPRESS)
            parser.add_argument('--query_execution_path', required=False, action='store', dest='query_execution_path', help=argparse.SUPPRESS)
            parser.add_argument('--credentials_path', required=False, action='store', dest='credentials_path', help=argparse.SUPPRESS)

            ## (Additional) Meteor Next Commands
            parser.add_argument('--deployment_id', required=False, action='store', dest='deployment_id', help=argparse.SUPPRESS)
            parser.add_argument('--deployment_mode', required=False, action='store', dest='deployment_mode', help=argparse.SUPPRESS)
            parser.add_argument('--execution_plan_factor', required=False, action='store', dest='execution_plan_factor', help=argparse.SUPPRESS)
            parser.add_argument('--user', required=False, action='store', dest='user', help=argparse.SUPPRESS)

            # App Internal Commands
            parser.add_argument('--uuid', required=False, action='store', dest='uuid', help=argparse.SUPPRESS)
            parser.add_argument('--env_id', required=False, action='store', dest='env_id', help=argparse.SUPPRESS)
            parser.add_argument('--env_check_sql', required=False, action='store', dest='env_check_sql', help=argparse.SUPPRESS)
            parser.add_argument('--env_compress', required=False, action='store_true', dest='env_compress', help=argparse.SUPPRESS)
            parser.add_argument('--env_start_deploy', required=False, action='store_true', dest='env_start_deploy', help=argparse.SUPPRESS)

            # Help Commands
            parser.add_argument('--usage', required=False, action='store_true', dest='usage', help='Show Meteor Usage')

            args = parser.parse_args()
            return args

        except Exception:
            raise Exception("Cannot init the Parser module.")
