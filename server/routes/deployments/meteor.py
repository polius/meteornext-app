import os
import sys
import json
import subprocess

import models.admin.settings
import models.inventory.environments
import models.inventory.regions
import models.inventory.servers
import models.inventory.auxiliary
import models.admin.groups

class Meteor:
    def __init__(self, sql, license):
        self._license = license
        # Init models
        self._settings = models.admin.settings.Settings(sql, license)
        self._environments = models.inventory.environments.Environments(sql, license)
        self._regions = models.inventory.regions.Regions(sql)
        self._servers = models.inventory.servers.Servers(sql, license)
        self._auxiliary = models.inventory.auxiliary.Auxiliary(sql)
        self._groups = models.admin.groups.Groups(sql)

        # Retrieve base path
        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._base_path = os.path.realpath(os.path.dirname(sys.executable)) if self._bin else os.path.realpath(os.path.dirname(sys.argv[0]))

    def execute(self, deployment):
        # Create Deployment Folder to store Meteor files
        if not os.path.isdir(f"{self._base_path}/files/deployments/{deployment['uri']}/keys"):
            os.makedirs(f"{self._base_path}/files/deployments/{deployment['uri']}/keys")

        # Compile Meteor Files
        self.__compile_config(deployment)
        self.__compile_blueprint(deployment)

        # Execute Meteor
        self.__execute(deployment)

    def __compile_config(self, deployment):
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
        keys_path = f"{self._base_path}/files/deployments/{deployment['uri']}/keys"

        for region in regions:
            # Compile SSH
            region_data = {
                "id": region['id'],
                "name": region['name'],
                "shared": region['shared'],
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
                        "id": server['id'],
                        "name": server['name'],
                        "shared": server['shared'],
                        "engine": server['engine'],
                        "hostname": server['hostname'],
                        "username": server['username'],
                        "password": server['password'],
                        "port": int(server['port']),
                        "ssl_ca_certificate": server['ssl_ca_certificate'],
                        "ssl_client_certificate": server['ssl_client_certificate'],
                        "ssl_client_key": server['ssl_client_key']
                    })

            # Add region data to the credentials
            config['regions'].append(region_data)

        # Compile Auxiliary Connections
        config['auxiliary_connections'] = {}
        for aux in auxiliary:
            if aux['name'] not in config['auxiliary_connections'] or not aux['shared']:
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
                        "ssl_client_key": aux['ssl_client_key']
                    }
                }

        # Generate key files
        for key in keys:
            with open(key['path'], 'w') as outfile:
                outfile.write(key['data'])
            os.chmod(key['path'], 0o600)

        # Compile Amazon S3
        amazon_s3 = json.loads(self._settings.get(setting_name='AMAZON'))

        config['amazon_s3'] = {
            "enabled": False,
            "aws_access_key_id": "",
            "aws_secret_access_key": "",
            "region_name": "",
            "bucket_name": ""
        }

        if amazon_s3['enabled']:
            config['amazon_s3'] = {
                "enabled": True,
                "aws_access_key_id": amazon_s3['aws_access_key'],
                "aws_secret_access_key": amazon_s3['aws_secret_access_key'],
                "region_name": amazon_s3['region'],
                "bucket_name": amazon_s3['bucket']
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
        with open(f"{self._base_path}/server.conf") as outfile:
            next_credentials = json.load(outfile)

        # Compile Meteor Next Credentials
        config['meteor_next'] = {
            "enabled": True,
            "hostname": next_credentials['sql']['hostname'],
            "port": int(next_credentials['sql']['port']),
            "username": next_credentials['sql']['username'],
            "password": next_credentials['sql']['password'],
            "database": next_credentials['sql']['database'],
            "ssl_ca_certificate": None,
            "ssl_client_certificate": None,
            "ssl_client_key": None
        }

        # Compile Meteor Next Params
        config['params'] = {
            "id": deployment['id'],
            "mode": deployment['mode'].lower(),
            "user": deployment['username'],
            "threads": deployment['execution_threads'],
            "timeout": deployment['execution_timeout'],
            'name': deployment['name'],
            "release": deployment['release'],
            "environment": deployment['environment_name'],
            "url": deployment['url']
        }

        # Compile Sentry
        config['sentry'] = {"enabled": False}
        if self._license.get_sentry():
            config['sentry']['enabled'] = True
            config['sentry']['environment'] = next_credentials['license']['access_key']

        # Store Config
        with open(f"{self._base_path}/files/deployments/{deployment['uri']}/config.json", 'w') as outfile:
            json.dump(config, outfile)

    def __compile_blueprint(self, deployment):
        if deployment['mode'] == 'BASIC':
            blueprint = self.__compile_blueprint_basic(deployment)
        elif deployment['mode'] == 'PRO':
            blueprint = deployment['code']

        # Store Query Execution
        with open(f"{self._base_path}/files/deployments/{deployment['uri']}/blueprint.py", 'w', encoding="utf-8") as outfile:
            outfile.write(blueprint.encode('utf-8','ignore').decode('utf-8'))

    def __compile_blueprint_basic(self, deployment):
        queries = {}
        for i, q in enumerate(json.loads(deployment['queries'])):
            queries[str(i+1)] = q['q']
        databases = [i.strip().replace('%','*').replace('_','?').replace('\\?','_') for i in  deployment['databases'].split(',')]
        return """import fnmatch
class blueprint:
    def __init__(self):
        self.queries = {0}
        self.auxiliary_queries = {{}}
    def before(self, meteor, environment, region, server):
        pass
    def main(self, meteor, environment, region, server, database):
        for d in {1}:
            if len(fnmatch.filter([database], d)) > 0:
                for i in self.queries.keys():
                    meteor.execute(query=self.queries[str(i)], database=database)
    def after(self, meteor, environment, region, server):
        pass""".format(json.dumps(queries), databases)

    def __execute(self, deployment):
        # Build Meteor Parameters
        meteor_base_path = sys._MEIPASS if self._bin else self._base_path
        meteor_path = [f"{meteor_base_path}/apps/meteor/init"] if self._bin else ["python3", f"{meteor_base_path}/../meteor/meteor.py"]
        execution_path = f"{self._base_path}/files/deployments/{deployment['uri']}"
        execution_method = deployment['method'].lower()

        # Build Meteor Command
        command = meteor_path + ["--path", execution_path, "--uri", deployment['uri'], f"--{execution_method}"]

        # Execute Meteor
        subprocess.Popen(command, stdout=subprocess.DEVNULL)
