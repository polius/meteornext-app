# -*- coding: utf-8 -*-
import os
import sys
import json
import uuid
import traceback
import logging
import argparse

from time import time
from datetime import datetime
from deploy import deploy
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

        # Print Header
        if self._args.env_id is None:
            self.__print_header()

        # Start Meteor Execution
        self.start()

    def start(self):
        try: 
            # Load the Core
            core = deploy(self._logger, self._args)

            # Remote Execution - Check SSH Connection
            core.check_remote_execution()
            
            # Init Core
            core.init()

        except KeyboardInterrupt:
            self._logger.warning("")
            self._logger.warning(colored("+==================================================================+", 'yellow'))
            self._logger.warning(colored("‖  WARNING                                                         ‖", 'yellow'))
            self._logger.warning(colored("+==================================================================+", 'yellow'))
            self._logger.warning("Program Interrupted By User.")
            core.clean()

        except Exception as e:
            self.__print_error()
            message = str(e).replace('[USER] ', '') if str(e).startswith('[USER] ') else str(e)
            self._logger.critical(colored("Message: ", attrs=['bold']) + message)
            if not str(e).startswith('[USER] '):
                self._logger.critical(colored("Showing Error Traceback ...", attrs=['bold']))
                self._logger.critical(traceback.format_exc())
            core.clean()

    ####################
    # Internal Methods #
    ####################
    def __print_header(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(colored(""" __  __ _____ _____ _____ ___  ____
|  \/  | ____|_   _| ____/ _ \|  _ \\
| |\/| |  _|   | | |  _|| | | | |_) |
| |  | | |___  | | | |__| |_| |  _ < 
|_|  |_|_____| |_| |_____\___/|_| \_\\ . [SQL] Mass Deployment Engine
    """, 'red', attrs=['bold']))

    def __print_error(self):
        self._logger.critical(colored("+==================================================================+", 'red', attrs=['bold']))
        self._logger.critical(colored("‖  ERROR                                                           ‖", 'red', attrs=['bold']))
        self._logger.critical(colored("+==================================================================+", 'red', attrs=['bold']))

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
            parser.add_argument('--environment', required=False, action='store', dest='environment', help='Select a valid environment from "credentials.json" file.')
            parser.add_argument('--servers', required=False, action='store', dest='servers', help='Select a valid environment from "credentials.json" file.')
            parser.add_argument('--validate', required=False, action='store', dest='validate', help='Validation of: Credentials + Query + Current Environment')
            parser.add_argument('--test', required=False, action='store_true', dest='test', help='Validation + Test Execution')
            parser.add_argument('--deploy', required=False, action='store_true', dest='deploy', help='Validation + Deployment')

            ## Additional Commands
            parser.add_argument('--logs_path', required=False, action='store', dest='logs_path', help='Set the Absolute Folder Path to store the Execution Files')
            parser.add_argument('--query_execution_path', required=False, action='store', dest='query_execution_path', help='Set the Absolute File Path to import the "query_execution.py" file')
            parser.add_argument('--credentials_path', required=False, action='store', dest='credentials_path', help='Set the Absolute File Path to import the "credentials.json" file')

            ## (Additional) Meteor Next Commands
            parser.add_argument('--deployment_id', required=False, action='store', dest='deployment_id', help='Set the Deployment ID to Log the Execution Progress')
            parser.add_argument('--deployment_mode', required=False, action='store', dest='deployment_mode', help='Set the Deployment Mode to Log the Execution Progress')
            parser.add_argument('--execution_plan_factor', required=False, action='store', dest='execution_plan_factor', help='Set the Execution Plan Factor Condition to All Select Queries')

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
