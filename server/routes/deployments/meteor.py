#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp
import json

class Meteor:
    def __init__(self, credentials):
        self._mysql = imp.load_source('mysql', '{}/models/mysql.py'.format(credentials['path'])).mysql(credentials)
        # Init models
        self._environments = imp.load_source('environments', '{}/models/deployments/environments.py'.format(credentials['path'])).Environments(credentials)
        self._regions = imp.load_source('regions', '{}/models/deployments/regions.py'.format(credentials['path'])).Regions(credentials)
        self._servers = imp.load_source('servers', '{}/models/deployments/servers.py'.format(credentials['path'])).Servers(credentials)
        self._auxiliary = imp.load_source('auxiliary', '{}/models/deployments/auxiliary.py'.format(credentials['path'])).Auxiliary(credentials)
        self._slack = imp.load_source('slack', '{}/models/deployments/slack.py'.format(credentials['path'])).Slack(credentials)
        self._s3 = imp.load_source('s3', '{}/models/deployments/s3.py'.format(credentials['path'])).S3(credentials)
        self._web = imp.load_source('web', '{}/models/deployments/web.py'.format(credentials['path'])).Web(credentials)

        # Init Meteor Files
        self._query_execution = ''
        self._credentials = {}

    def execute(self, deployment):
        print(deployment)
        # Compile Metadata
        self.__compile_credentials(deployment)
        self.__compile_query_execution(deployment)

        # Execute Meteor
        self.__execute()

    def __compile_credentials(self, deployment):
        # Get Data
        environments = self._environments.get(deployment['group_id'])
        regions = self._regions.get(deployment['group_id'])
        servers = self._servers.get(deployment['group_id'])
        auxiliary = self._auxiliary.get(deployment['group_id'])
        slack = self._slack.get(deployment['group_id'])
        s3 = self._s3.get(deployment['group_id'])
        web = self._web.get(deployment['group_id'])

        # Compile [Environments, Regions, Servers]
        self._credentials['environments'] = {}

        for environment in environments:
            self._credentials['environments'][environment['name']] = {}
            for region in regions:
                if region['environment_id'] == environment['id']:
                    self._credentials['environments'][environment['name']]['region'] = region['name']
                    self._credentials['environments'][environment['name']]['ssh'] = {
                        "enabled": "True" if region['cross_region'] == 1 else "False",
                        "hostname": region['hostname'],
                        "username": region['username'],
                        "password": "" if region['password'] == None else region['password'],
                        "key": "",
                        "deploy_path": region['deploy_path']
                    }
                    for server in servers:
                        if server['environment_id'] == environment['id'] and server['region_id'] == region['id']:
                            self._credentials['environments'][environment['name']]['sql'] = {
                                "name": server['name'],
                                "hostname": server['hostname'],
                                "username": server['username'],
                                "password": server['password']
                            }

        # Compile Auxiliary Connections
        self._credentials['auxiliary_connections'] = {}
        for aux in auxiliary:
            self._credentials['auxiliary_connections'][aux['name']] = {
                "hostname": aux['hostname'],
                "username": aux['username'],
                "password": aux['password']
            }

        # Compile Slack
        self._credentials['slack'] = {
            "enabled": "False",
            "webhook": ""
        }
        if len(slack) > 0:
            self._credentials['slack'] = {
                "enabled": "True" if slack[0]['enabled'] == 1 else 'False',
                "webhook": slack[0]['webhook']
            }
        
        # Compile Amazon S3
        self._credentials['s3'] = {
            "enabled": "False",
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
            "region_name": "",
            "bucket_name": ""
        }
        if len(s3) > 0:
            self._credentials['s3'] = {
                "enabled": "True" if s3[0]['enabled'] == 1 else "False",
                "aws_access_key_id": s3[0]['aws_access_key'],
                "aws_secret_access_key": s3[0]['aws_secret_access_key'],
                "region_name": s3[0]['region_name'],
                "bucket_name": s3[0]['bucket_name']
            }
        
        # Compile Web
        self._credentials['web'] = {
            "public_url": ""
        }
        if len(web) > 0:
            self._credentials['web'] = {
                "public_url": web[0]['url']
            }
        
        # Compile Execution Mode
        self._credentials['execution_mode'] = {
            "parallel": "True" if deployment['execution'] == 'PARALLEL' else 'False',
            "threads": str(deployment['execution_threads']) if deployment['execution'] == 'PARALLEL' else ''
        }

        print(self._credentials)

    def __compile_query_execution(self, deployment):
        queries = {}
        for i, q in enumerate(deployment['queries']):
            queries[str(i+1)] = q['query']

        self._query_execution = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
import fnmatch
class query_execution:
    def __init__(self, query_instance=None):
        self._meteor = query_instance
        self._queries = {}
        self._auxiliary_queries = {{}}
    def before(self, environment, region):
        pass
    def main(self, environment, region, server, database):
        if len(fnmatch.filter([database], '{}')) > 0:
            for i in self._queries.keys():
                self._meteor.execute(query=self._queries[str(i)], database=database)
    def after(self, environment, region):
        pass
    @property
    def queries(self):
        return self._queries
    @property
    def auxiliary_queries(self):
        return self._auxiliary_queries
    def set_query(self, query_instance):
        self._meteor = query_instance""".format(json.dumps(queries), deployment['databases'])

        print(self._query_execution)

    def __execute(self):
        pass