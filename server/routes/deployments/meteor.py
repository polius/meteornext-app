import os
import sys
import json
import uuid
import subprocess
import unicodedata
from time import time
from datetime import datetime
from multiprocessing import Process

import models.admin.settings
import models.inventory.environments
import models.inventory.regions
import models.inventory.servers
import models.inventory.auxiliary
import models.admin.groups

class Meteor:
    def __init__(self, app, sql, license):
        self._app = app

        # Init models
        self._settings = models.admin.settings.Settings(sql)
        self._environments = models.inventory.environments.Environments(sql, license)
        self._regions = models.inventory.regions.Regions(sql)
        self._servers = models.inventory.servers.Servers(sql, license)
        self._auxiliary = models.inventory.auxiliary.Auxiliary(sql)
        self._groups = models.admin.groups.Groups(sql)

        # Retrieve Meteor Files Path
        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._base_path = os.path.dirname(sys.executable) if self._bin else app.root_path

    def execute(self, deployment):
        # Generate Deployment Unique Identifier
        uri = str(uuid.uuid4())

        # Init Files Settings
        files = json.loads(self._settings.get(setting_name='FILES'))

        # Create Deployment Folder to store Meteor files
        if not os.path.isdir('{}/deployments/{}/keys'.format(files['local']['path'], uri)):
            os.makedirs('{}/deployments/{}/keys'.format(files['local']['path'], uri))

        # Compile Meteor Files
        self.__compile_config(deployment, files, uri)
        self.__compile_blueprint(deployment, files, uri)

        # Execute Meteor
        self.__execute(deployment, files, uri)

    def __compile_config(self, deployment, files, uri):
        # Get Data
        environment = self._environments.get(deployment['user_id'], deployment['group_id'], deployment['environment_id'])
        regions = self._regions.get_by_environment(deployment['user_id'], deployment['group_id'], deployment['environment_id'])
        servers = self._servers.get_by_environment(deployment['user_id'], deployment['group_id'], deployment['environment_id'])
        auxiliary = self._auxiliary.get(deployment['user_id'], deployment['group_id'])
        slack = self._groups.get_slack(deployment['group_id'])

        if len(environment) == 0:
            return
    
        # Compile Regions
        config = {'regions': []}

        # Generate Keys Base Path
        keys = []
        keys_path = "{}/deployments/{}/keys".format(files['local']['path'], uri)

        for region in regions:
            # Compile SSH
            region_data = {
                "id": region['id'],
                "name": region['name'],
                "ssh": {
                    "enabled": True if region['ssh_tunnel'] else False,
                    "hostname": "" if region['hostname'] is None else region['hostname'],
                    "username": "" if region['username'] is None else region['username'],
                    "password": "" if region['password'] is None else region['password'],
                    "key": "",
                    "port": "" if region['port'] is None else region['port'],
                },
                "sql": []
            }
            # Parse Keys
            if region['key']:
                keys.append({"path": f"{keys_path}/r{region['id']}.ssh_key", "data": region['key']})
                region_data['ssh']['key'] = f"{keys_path}/r{region['id']}.ssh_key"

            # Compile SQL
            for server in servers:
                if server['region_id'] == region['id']:
                    # Init Server Conf
                    region_data['sql'].append({
                        "name": server['name'],
                        "engine": server['engine'],
                        "hostname": server['hostname'],
                        "username": server['username'],
                        "password": server['password'],
                        "port": int(server['port']),
                        "ssl_ca_certificate": server['ssl_ca_certificate'],
                        "ssl_client_certificate": server['ssl_client_certificate'],
                        "ssl_client_key": server['ssl_client_key'],
                        "ssl_verify_ca": server['ssl_verify_ca'] == 1
                    })

            # Add region data to the credentials
            config['regions'].append(region_data)

        # Compile Auxiliary Connections
        config['auxiliary_connections'] = {}
        for aux in auxiliary:
            # Init Auxiliary Conf
            config['auxiliary_connections'][aux['name']] = {
                "ssh": { "enabled": False },
                "sql": {
                    "engine": aux['engine'],
                    "hostname": aux['hostname'],
                    "username": aux['username'],
                    "password": aux['password'],
                    "port": int(aux['port']),
                    "ssl_ca_certificate": aux['ssl_ca_certificate'],
                    "ssl_client_certificate": aux['ssl_client_certificate'],
                    "ssl_client_key": aux['ssl_client_key'],
                    "ssl_verify_ca": aux['ssl_verify_ca']
                }
            }

        # Generate key files
        for key in keys:
            with open(key['path'], 'w') as outfile:
                outfile.write(key['data'])
            os.chmod(key['path'], 0o600)

        # Compile Amazon S3
        config['amazon_s3'] = {
            "enabled": False,
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
            "region_name": "",
            "bucket_name": ""
        }

        if 'amazon_s3' in files and files['amazon_s3']['enabled']:
            config['amazon_s3'] = {
                "enabled": True,
                "aws_access_key_id": files['amazon_s3']['aws_access_key'],
                "aws_secret_access_key": files['amazon_s3']['aws_secret_access_key'],
                "region_name": files['amazon_s3']['region'],
                "bucket_name": files['amazon_s3']['bucket']
            }

        # Compile Slack
        config['slack'] = {
            "enabled": False,
            "channel_name": "",
            "webhook_url": ""
        }
        if slack['enabled']:
            config['slack'] = {
                "enabled":  True if slack['enabled'] else False,
                "channel_name": slack['channel_name'],
                "webhook_url": slack['webhook_url']
            }

        # Enable Meteor Next
        with open("{}/server.conf".format(self._base_path)) as outfile:
            next_credentials = json.load(outfile)['sql']

        # Compile Meteor Next Credentials
        config['meteor_next'] = {
            "enabled": True,
            "hostname": next_credentials['hostname'],
            "port": int(next_credentials['port']),
            "username": next_credentials['username'],
            "password": next_credentials['password'],
            "database": next_credentials['database'],
            "ssl_ca_certificate": None,
            "ssl_client_certificate": None,
            "ssl_client_key": None,
            "ssl_verify_ca": None
        }

        # Compile Meteor Next Params
        config['params'] = {
            "id": deployment['id'],
            "mode": deployment['mode'].lower(),
            "user": deployment['username'],
            "threads": deployment['execution_threads'],
            "timeout": deployment['execution_timeout'],
            "environment": deployment['environment_name'],
            "url": deployment['url']
        }

        # Store Config
        with open("{}/deployments/{}/config.json".format(files['local']['path'], uri), 'w') as outfile:
            json.dump(config, outfile)

    def __compile_blueprint(self, deployment, files, uri):
        if deployment['mode'] == 'BASIC':
            blueprint = self.__compile_blueprint_basic(deployment)
        elif deployment['mode'] == 'PRO':
            blueprint = deployment['code']

        # Store Query Execution
        with open("{}/deployments/{}/blueprint.py".format(files['local']['path'], uri), 'w', encoding="utf-8") as outfile:
            outfile.write(blueprint.encode('utf-8','ignore').decode('utf-8'))

    def __compile_blueprint_basic(self, deployment):
        queries = {}
        for i, q in enumerate(json.loads(deployment['queries'])):
            queries[str(i+1)] = q['query']
        databases = [i.strip().replace('%','*').replace('_','?').replace('\\?','_') for i in  deployment['databases'].split(',')]
        return """import fnmatch
class blueprint:
    def __init__(self):
        self.queries = {0}
        self.auxiliary_queries = {{}}
    def before(self, meteor, environment, region):
        pass
    def main(self, meteor, environment, region, server, database):
        for d in {1}:
            if len(fnmatch.filter([database], d)) > 0:
                for i in self.queries.keys():
                    meteor.execute(query=self.queries[str(i)], database=database)
    def after(self, meteor, environment, region):
        pass""".format(json.dumps(queries), databases)

    def __execute(self, deployment, files, uri):
        # Build Meteor Parameters
        meteor_base_path = sys._MEIPASS if self._bin else self._app.root_path
        meteor_path = "{}/apps/meteor/init".format(meteor_base_path) if self._bin else "python3 {}/../meteor/meteor.py".format(meteor_base_path)
        execution_path = "{}/deployments/{}".format(files['local']['path'], uri)
        execution_method = deployment['method'].lower()

        # Build Meteor Command
        command = '{} --path "{}" --{}'.format(meteor_path, execution_path, execution_method)

        # Execute Meteor
        # p = subprocess.Popen(command, shell=True)
        p = subprocess.Popen(command, stdout=open('/dev/null', 'w'), shell=True)
