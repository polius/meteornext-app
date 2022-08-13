from flask import Blueprint, jsonify, request
import os
import sys
import copy
import json
import uuid
import boto3
import bcrypt
import tempfile

import models.admin.settings
import connectors.base
import models.admin.users

class Install:
    def __init__(self, license, conf, blueprints):
        self._license = license
        self._conf = conf
        self._blueprints = blueprints
        self._available = None
        # Retrieve base path
        self._bin = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._base_path = os.path.realpath(os.path.dirname(sys.executable)) if self._bin else os.path.realpath(os.path.dirname(sys.argv[0]))

    def blueprint(self):
        # Init blueprint
        install_blueprint = Blueprint('install', __name__, template_folder='install')

        @install_blueprint.route('/install', methods=['GET','POST'])
        def install_method():
            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post()

        @install_blueprint.route('/install/license', methods=['POST'])
        def install_license_method():
            # Protect api call once is already configured
            if not self.available():
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            data = request.get_json()

            # Set unique hardware id
            data['uuid'] = str(uuid.getnode())

            # Check License
            self._license.set_license(data)
            self._license.validate(force=True)
            return jsonify({"message": self._license.get_status()['response']}), self._license.get_status()['code']

        @install_blueprint.route('/install/sql', methods=['POST'])
        def install_sql_method():
            # Protect api call once is already configured
            if not self.available():
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            data = request.get_json()

            # Check SQL Credentials
            try:
                sql = connectors.base.Base({'ssh': {'enabled': False}, 'sql': data})
                sql.test_sql()
                return jsonify({'message': 'Connection Successful.', 'exists': True}), 200
            except Exception as e:
                if "Unknown database " in str(e):
                    return jsonify({'message': 'Connection Successful.', 'exists': False}), 200
                return jsonify({'message': str(e)}), 400

        @install_blueprint.route('/install/amazon', methods=['POST'])
        def install_amazon_method():
            # Protect api call once is already configured
            if not self.available():
                return jsonify({}), 401

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400

            # Get Params
            data = request.get_json()

            # Check Amazon Credentials
            file = tempfile.NamedTemporaryFile()
            file.write('This file has been created by Meteor Next to validate the credentials.\nIt is safe to delete it.'.encode())
            file.flush()
            # Init the boto3 client with the provided credentials
            client = boto3.client(
                service_name='s3', 
                region_name=data['region'],
                aws_access_key_id=data['aws_access_key'],
                aws_secret_access_key=data['aws_secret_access_key']
            )
            try:
                client.upload_file(file.name, data['bucket'], 'test.txt')
                client.get_object(Bucket=data['bucket'], Key='test.txt')
                return jsonify({'message': 'Credentials Validated.'}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 400
            finally:
                file.close()

        return install_blueprint

    ####################
    # Internal Methods #
    ####################
    def available(self):
        if self._available is None:
            conf_path = f"{self._base_path}/server.conf"
            if os.path.exists(conf_path):
                with open(conf_path) as file_open:
                    f = json.load(file_open)
                    if f['sql']['hostname'] != '' and f['sql']['username'] != '' and f['sql']['password'] != '' and f['sql']['port'] != '' and f['sql']['database'] != '':
                        self._available = False
            else:
                self._available = True
        return self._available

    def get(self):
        return jsonify({'setup_required': self.available()}), 200

    def post(self):
        # Protect api call once is already configured
        if not self.available():
            return jsonify({}), 401

        if not request.is_json:
            return jsonify({"message": "Missing JSON in request"}), 400

        # Get Params
        data = request.get_json()

        # Build Meteor & Create User Admin Account
        if data['sql']['recreate']:
            # Init sql connection
            sql_conf = copy.deepcopy(data['sql'])
            sql_conf['database'] = None
            sql = connectors.base.Base({'ssh': {'enabled': False}, 'sql': sql_conf})

            # Import SQL Schema
            sql.execute('DROP DATABASE IF EXISTS `{}`'.format(data['sql']['database']))
            sql.execute('CREATE DATABASE `{}`'.format(data['sql']['database']))
            schema_file = f"{sys._MEIPASS}/models/schema.sql" if self._bin else f"{self._base_path}/models/schema"
            with open(schema_file) as file_open:
                queries = file_open.read().split(';')
                for q in queries:
                    if q.strip() != '':
                        sql.execute(query=q, database=data['sql']['database'])

            # Create group
            groups = models.admin.groups.Groups(sql)
            group = {"name": 'Administrator', "description": 'The Admin', "coins_day": 25, "coins_max": 100, "inventory_enabled": 1, "deployments_enabled": 1, "deployments_basic": 1, "deployments_pro": 1, "deployments_coins": 10, "deployments_execution_concurrent": 1, "deployments_execution_threads": 10, "deployments_execution_timeout": None, "deployments_expiration_days": 30, "deployments_slack_enabled": 0, "deployments_slack_name": None, "deployments_slack_url": None, "monitoring_enabled": 1, "monitoring_interval": 10, "utils_enabled": 1, "utils_coins": 10, "utils_concurrent": 1, "utils_limit": None, "utils_slack_enabled": 0, "utils_slack_name": None, "utils_slack_url": None, "client_enabled": 1, "client_limits": 0, "client_limits_timeout_mode": 1, "client_limits_timeout_value": 10, "client_limits_rows": 1000, "client_tracking": 0, "client_tracking_retention": 1, "client_tracking_mode": 1}
            groups.post(1, group)

            # Create user
            users = models.admin.users.Users(sql)
            user = {"username": data['account']['username'], "password": data['account']['password'], "email": "admin@admin.com", "coins": 100, "group": 'Administrator', "admin": 1, "disabled": 0, "change_password": 0}
            user['password'] = bcrypt.hashpw(user['password'].encode('utf8'), bcrypt.gensalt())
            users.post(1, user)

            # Init Amazon S3
            settings = models.admin.settings.Settings(sql, self._license)
            if data['amazon']['enabled']:
                setting = {"name": "AMAZON", "value": f'{{"enabled":true,"aws_access_key":"{data["amazon"]["aws_access_key"]}","aws_secret_access_key":"{data["amazon"]["aws_secret_access_key"]}","region":"{data["amazon"]["region"]}","bucket":"{data["amazon"]["bucket"]}"}}'}
                settings.post(user_id=1, setting=setting)

        # Create keys folder
        keys_path = f"{self._base_path}/keys"
        if not os.path.exists(keys_path):
            os.makedirs(keys_path)

        # Write setup to the setup file
        self._conf["license"] = {
            "access_key": data['license']['access_key'],
            "secret_key": data['license']['secret_key']
        }
        self._conf["sql"] = {
            "engine": data['sql']['engine'],
            "hostname": data['sql']['hostname'],
            "port": int(data['sql']['port']),
            "username": data['sql']['username'],
            "password": data['sql']['password'],
            "database": data['sql']['database'],
            "ssl_client_key": None,
            "ssl_client_certificate": None,
            "ssl_ca_certificate": None,
            "ssl_verify_ca": data['sql']['ssl_verify_ca']
        }
        if data['sql']['ssl_client_key']:
            with open(f"{keys_path}/ssl_key.pem", 'w') as outfile:
                outfile.write(data['sql']['ssl_client_key'])
            self._conf['sql']['ssl_client_key'] = 'ssl_key.pem'
        if data['sql']['ssl_client_certificate']:
            with open(f"{keys_path}/ssl_cert.pem", 'w') as outfile:
                outfile.write(data['sql']['ssl_client_certificate'])
            self._conf['sql']['ssl_client_certificate'] = 'ssl_cert.pem'
        if data['sql']['ssl_ca_certificate']:
            with open(f"{keys_path}/ssl_ca.pem", 'w') as outfile:
                outfile.write(data['sql']['ssl_ca_certificate'])
            self._conf['sql']['ssl_ca_certificate'] = 'ssl_ca.pem'
        with open(f"{self._base_path}/server.conf", 'w') as outfile:
            json.dump(self._conf, outfile)

        # Init sql pool
        sql = connectors.pool.Pool(self._conf['sql'])

        # Init blueprints
        for k,v in self._blueprints.items():
            if k == 'settings':
                v.init(sql, self._conf)
            else:
                v.init(sql)

        # Set unique hardware id
        self._conf['license']['uuid'] = str(uuid.getnode())

        # Disable Install
        self._available = False

        # Build return message
        return jsonify({'message': 'Welcome to Meteor Next!'}), 200
