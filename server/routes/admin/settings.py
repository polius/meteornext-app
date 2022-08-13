import os
import re
import json
import boto3
import tempfile
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.admin.settings

class Settings:
    def __init__(self, license, sql=None):
        self._license = license
        if sql:
            self.init(sql)

    def init(self, sql, conf=None):
        self._settings_conf = conf
        # Init models
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql, self._license)

    def blueprint(self):
        # Init blueprint
        settings_blueprint = Blueprint('settings', __name__, template_folder='settings')

        @settings_blueprint.route('/admin/settings', methods=['GET','POST'])
        @jwt_required()
        def settings_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user['id'])

        @settings_blueprint.route('/admin/settings/license', methods=['GET'])
        @jwt_required()
        def settings_license_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check number of seconds elapsed before last check
            now = datetime.utcnow()
            last = self._license.get_last_check_date()
            diff = int((now-last).total_seconds())

            # Check license status
            if int(diff) >= 60:
                self._license.validate(force=True)

            # Build data
            license = {
                "account": self._license.get_status()['account'],
                "access_key": self._settings_conf['license']['access_key'],
                "secret_key": self._settings_conf['license']['secret_key'],
                "resources": self._license.get_status()['resources'],
                "last_check_date": self._license.get_last_check_date(),
            }
            if int(diff) < 60:
                return jsonify({'license': license, 'message': f"Wait {60-diff} seconds to refresh again"}), 400
            else:
                return jsonify({'license': license}), 200

        @settings_blueprint.route('/admin/settings/license/usage', methods=['GET'])
        @jwt_required()
        def settings_license_usage_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Return usage
            usage = self._settings.get_license_usage()
            return jsonify({'usage': usage}), 200

        @settings_blueprint.route('/admin/settings/amazon/test', methods=['POST'])
        @jwt_required()
        def settings_files_test_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            settings_json = request.get_json()

            # Test Amazon S3 Credentials
            return self.test_amazon_credentials(settings_json)

        return settings_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self):
        # Init Settings
        settings = {}
        s = self._settings.get()

        # Get License Settings
        settings['license'] = {}
        settings['license']['account'] = self._license.get_status()['account']
        settings['license']['access_key'] = self._settings_conf['license']['access_key']
        settings['license']['secret_key'] = self._settings_conf['license']['secret_key']
        settings['license']['resources'] = self._license.get_status()['resources']
        settings['license']['last_check_date'] = self._license.get_last_check_date()

        # Get SQL Settings
        settings['sql'] = self._settings_conf['sql']

        # Get Security / Amazon / Advanced
        settings['amazon'] = {}
        settings['security'] = {}
        settings['advanced'] = {}
        for i in s:
            if i['name'] in ['SECURITY', 'AMAZON', 'ADVANCED']:
                settings[i['name'].lower()] = json.loads(i['value'])

        # Get current Domain URL from Security
        regex = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
        r = re.search(regex, request.url_root)
        ip = r['host'] + ':' + r['port'] if len(r['port']) > 0 else r['host']
        settings['security']['current'] = ip

        # Return Settings
        return jsonify({'settings': settings}), 200

    def post(self, user_id):
        # Get data
        data = request.get_json()
        # Store Setting
        setting = {
            'name': data['name'],
            'value': json.dumps(data['value'])
        }
        self._settings.post(user_id, setting)
        return jsonify({'message': 'Changes saved'}), 200

    def check_url(self, security=None):
        if security is None:
            security = self._settings.get(setting_name='SECURITY')
        data = json.loads(security)
        if 'restrict_url' in data and len(data['restrict_url']) > 0:
            regex = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
            # Current URL
            r = re.search(regex, request.url_root)
            current_url = r['host'] + ':' + r['port'] if len(r['port']) > 0 else r['host']
            # Administration URL
            r = re.search(regex, data['restrict_url'])
            admin_url = r['host'] + ':' + r['port'] if len(r['port']) > 0 else r['host']
            # Check URLs
            if current_url != admin_url:
                return False
        return True
    
    def check_mfa(self, security=None):
        if security is None:
            security = self._settings.get(setting_name='SECURITY')
        data = json.loads(security)
        if 'force_mfa' in data and data['force_mfa'] is True:
            return True
        return False

    def test_amazon_credentials(self, data):
        # Generate Temp File
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
            return jsonify({'message': 'Credentials validated'}), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 400
        finally:
            # Close the Temp File
            file.close()
