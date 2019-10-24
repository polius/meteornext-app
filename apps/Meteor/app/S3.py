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
            print(colored("+==================================================================+", "magenta", attrs=['bold']))
            print(colored("‖  AMAZON S3                                                       ‖", "magenta", attrs=['bold']))
            print(colored("+==================================================================+", "magenta", attrs=['bold']))

            try:
                # Upload Logs to S3
                status_msg = "- Uploading Logs to S3 Bucket '{}'...".format(self._credentials['s3']['bucket_name'])
                print(status_msg)
                self._progress.track_logs("Uploading Logs to Amazon S3...")

                # 1. Upload Compressed Logs Folder to '/logs'
                file_path = "{}/{}{}.tar.gz".format(self._args.logs_path, deploy_prefix, deploy_name)
                bucket_name = self._credentials['s3']['bucket_name']
                s3_path = "logs/{}{}.tar.gz".format(deploy_prefix, deploy_name)
                self.__s3.meta.client.upload_file(file_path, bucket_name, s3_path)

                # 2. Upload Results File to '/results'
                file_path = "{}/{}/meteor.js".format(self._args.logs_path, deploy_name)
                s3_path = "results/{}.js".format(uuid)
                self.__s3.meta.client.upload_file(file_path, bucket_name, s3_path)

            except Exception as e:
                self._logger.error(colored("- Uploading Process Failed.", 'red', attrs=['bold', 'reverse']))
                self._logger.error(e)
