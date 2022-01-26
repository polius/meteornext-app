import os
import re
import json
import boto3
import tempfile
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.admin.settings

class Settings:
    def __init__(self, app, sql, license, settings=None):
        self._app = app
        self._sql = sql
        self._license = license
        self._settings_conf = settings
        # Init models
        self._users = models.admin.users.Users(sql)
        self._settings = models.admin.settings.Settings(sql, license)

    def blueprint(self):
        # Init blueprint
        settings_blueprint = Blueprint('settings', __name__, template_folder='settings')

        @settings_blueprint.route('/admin/settings', methods=['GET','POST'])
        @jwt_required()
        def settings_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            settings_json = request.get_json()

            if request.method == 'GET':
                return self.get()
            elif request.method == 'POST':
                return self.post(user['id'], settings_json['name'], settings_json['value'])

        @settings_blueprint.route('/admin/settings/license', methods=['GET'])
        @jwt_required()
        def settings_license_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['admin']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check number of seconds elapsed before last check
            now = datetime.utcnow()
            last = self._license.last_check_date
            diff = int((now-last).total_seconds())

            # Check license status
            if int(diff) >= 60:
                self._license.validate(force=True)

            # Build data
            license = {
                "access_key": self._settings_conf['license']['access_key'],
                "secret_key": self._settings_conf['license']['secret_key'],
                "resources": self._license.status['resources'],
                "last_check_date": self._license.last_check_date,
            }
            if int(diff) < 60:
                return jsonify({'license': license, 'message': f"Wait {60-diff} seconds to refresh again"}), 400
            else:
                return jsonify({'license': license}), 200

        @settings_blueprint.route('/admin/settings/license/usage', methods=['GET'])
        @jwt_required()
        def settings_license_usage_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

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
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Check Security (Administration URL)
            if not self.check_url():
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

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
        settings['license']['access_key'] = self._settings_conf['license']['access_key']
        settings['license']['secret_key'] = self._settings_conf['license']['secret_key']
        settings['license']['resources'] = self._license.status['resources']
        settings['license']['last_check_date'] = self._license.last_check_date

        # Get SQL Settings
        settings['sql'] = self._settings_conf['sql']

        # Get Files / Security / Amazon / Deployments Settings
        settings['files'] = settings['amazon'] = settings['deployments'] = settings['security'] = {}
        settings['amazon'] = {}
        settings['deployments'] = {}
        settings['security'] = {}
        for i in s:
            if i['name'] in ['FILES', 'SECURITY', 'AMAZON', 'DEPLOYMENTS']:
                settings[i['name'].lower()] = json.loads(i['value'])

        # Get current Domain URL from Security
        regex = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
        r = re.search(regex, request.url_root)
        ip = r['host'] + ':' + r['port'] if len(r['port']) > 0 else r['host']
        settings['security']['current'] = ip

        # Return Settings
        return jsonify({'settings': settings}), 200

    def post(self, user_id, name, value):
        if name == 'FILES':
            # Check files path permissions
            if not self.check_files_path(value['path']):
                return jsonify({'message': 'No write permissions in the files folder'}), 400
        # Store Settings
        settings = {
            'name': name,
            'value': json.dumps(value)
        }
        self._settings.post(user_id, settings)
        return jsonify({'message': 'Changes saved'}), 200

    def check_url(self, security=None):
        if security is None:
            security = self._settings.get(setting_name='security')
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
            security = self._settings.get(setting_name='security')
        data = json.loads(security)
        if 'force_mfa' in data and data['force_mfa'] is True:
            return True
        return False

    def check_files_path(self, path):
        while not os.path.exists(path) and path != '/':
            path = os.path.normpath(os.path.join(path, os.pardir))
        if os.access(path, os.X_OK | os.W_OK):
            return True
        return False

    def test_amazon_credentials(self, data):
        # Generate Temp File
        file = tempfile.NamedTemporaryFile()
        file.write('This file has been created by Meteor Next to validate the credentials (Administration --> Settings --> Files).\nIt is safe to delete it.'.encode())
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
