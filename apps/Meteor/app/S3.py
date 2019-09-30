#!/usr/bin/env python
# -*- coding: utf-8 -*-
import boto3
import botocore
import os
import json
import copy
from colors import colored


class S3:
    def __init__(self, logger, args, credentials, progress):
        self._logger = logger
        self._args = args
        self._credentials = credentials
        self._progress = progress

        if self._credentials['s3']['enabled'] == 'True':
            session = boto3.Session(
                aws_access_key_id=self._credentials['s3']['aws_access_key_id'],
                aws_secret_access_key=self._credentials['s3']['aws_secret_access_key'],
                region_name=self._credentials['s3']['region_name']
            )
            self.__s3 = session.resource('s3')

    def upload_logs(self, deploy_name, deploy_prefix, uuid):
        # Upload Logs to S3
        if self._credentials['s3']['enabled'] == 'True':
            self._logger.info(colored("+==================================================================+", "magenta", attrs=['bold']))
            self._logger.info(colored("‖  AMAZON S3                                                       ‖", "magenta", attrs=['bold']))
            self._logger.info(colored("+==================================================================+", "magenta", attrs=['bold']))
            script_path = os.path.dirname(os.path.realpath(__file__))
            
            # Anonymizing Credentials
            # self._logger.info("- Anonymizing Credentials...")
            # self.__anonymize_credentials("{}/logs/{}/".format(script_path, deploy_name))

            # Upload Logs to S3
            try:
                status_msg = "- Uploading Logs to S3 Bucket '{}'...".format(self._credentials['s3']['bucket_name'])
                self._logger.info(status_msg)
                self._progress.track(key='logs', value=status_msg)

                # 1. Upload Compressed Logs Folder to '/logs'
                file_path = "{}/logs/{}{}.tar.gz".format(script_path, deploy_prefix, deploy_name)
                bucket_name = self._credentials['s3']['bucket_name']
                s3_path = "logs/{}{}.tar.gz".format(deploy_prefix, deploy_name)
                self.__s3.meta.client.upload_file(file_path, bucket_name, s3_path)

                # 2. Upload Results File to '/web'
                file_path = "{}/logs/{}/meteor.js".format(script_path, deploy_name)
                s3_path = "web/{}.js".format(uuid)
                self.__s3.meta.client.upload_file(file_path, bucket_name, s3_path)

            except Exception as e:
                self._logger.error(colored("- Uploading Process Failed.", 'red', attrs=['bold', 'reverse']))
                self._logger.error(e)

    def __anonymize_credentials(self, deploy_path):
        credentials_anonymized = copy.deepcopy(self._credentials)   
        # Anonymize Environments (SSH + SQL)
        for env in credentials_anonymized['environments'].keys():
            for env_id in credentials_anonymized['environments'][env]:
                env_id['ssh']['username'] = ""
                env_id['ssh']['password'] = ""
                for sql in env_id['sql']:
                    sql['username'] = ""
                    sql['password'] = ""

        # Anonymize Auxiliary Connections
        for aux in credentials_anonymized['auxiliary_connections'].values():
            aux['username'] = ""
            aux['password'] = ""
        
        # Anonymize Slack Credentials
        credentials_anonymized['slack']['webhook'] = ""

        # Anonymize S3 Credentials
        credentials_anonymized['s3']['aws_access_key_id'] = ""
        credentials_anonymized['s3']['aws_secret_access_key'] = ""

        # Replace 'credentials.json' with the Anonymized Version
        with open(deploy_path + 'credentials.json', 'w') as credentials_file:
            credentials_file.write(json.dumps(credentials_anonymized, separators=(',', ':')))