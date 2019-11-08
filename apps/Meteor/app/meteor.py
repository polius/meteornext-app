#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import traceback
import logging
import argparse
import json
import sys
from time import time
from datetime import datetime
from deploy import deploy
from colors import colored


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    cls()
    print(colored(""" __  __ _____ _____ _____ ___  ____
|  \/  | ____|_   _| ____/ _ \|  _ \\
| |\/| |  _|   | | |  _|| | | | |_) |
| |  | | |___  | | | |__| |_| |  _ < 
|_|  |_|_____| |_| |_____\___/|_| \_\\ . [SQL] Mass Deployment Engine
""", 'red', attrs=['bold']))


def print_error(logger):
    logger.critical(colored("+==================================================================+", 'red', attrs=['bold']))
    logger.critical(colored("‖  ERROR                                                           ‖", 'red', attrs=['bold']))
    logger.critical(colored("+==================================================================+", 'red', attrs=['bold']))


def init_logger_stream():
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


def init_parser():
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


#########################################################################################################
# CORE START                                                                                            #
#########################################################################################################
try:
    # Init Logger Stream Handler
    logger = init_logger_stream()

    # Load the Parser
    args = init_parser()

    # Set the Default Logs Path (if it has not been set by the user)
    if args.logs_path is None:
        script_path = os.path.dirname(os.path.realpath(__file__))
        args.logs_path = '{}/logs/'.format(script_path)

    # Load the Core
    core = deploy(logger, args)

    # Print Header
    if args.env_id is None:
        print_header()

    # Remote Execution - Check SSH Connection
    core.check_remote_execution()
    
    # Init Core
    core.init()

except KeyboardInterrupt:
    logger.warning("")
    logger.warning(colored("+==================================================================+", 'yellow'))
    logger.warning(colored("‖  WARNING                                                         ‖", 'yellow'))
    logger.warning(colored("+==================================================================+", 'yellow'))
    logger.warning("Program Interrupted By User.")
    core.clean()

except Exception as e:
    print_error(logger)
    message = str(e).replace('[USER] ', '') if str(e).startswith('[USER] ') else str(e)
    logger.critical(colored("Message: ", attrs=['bold']) + message)
    if not str(e).startswith('[USER] '):
        logger.critical(colored("Showing Error Traceback ...", attrs=['bold']))
        logger.critical(traceback.format_exc())
    core.clean()
