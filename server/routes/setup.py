import os
import sys
import json
import bcrypt
import models.admin.users
import models.mysql
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

class Setup:
    def __init__(self, app):
        self._ROOT_PATH = app.root_path if sys.argv[0].endswith('.py') else os.path.dirname(sys.executable)
        self._setup_file = "{}/server.conf".format(self._ROOT_PATH)

    def blueprint(self):
        # Init blueprint
        setup_blueprint = Blueprint('setup', __name__, template_folder='setup')

        @setup_blueprint.route('/setup', methods=['GET'])
        def setup():
            if self.__setup_available():
                return jsonify({}), 200
            else:
                return jsonify({}), 401

        @setup_blueprint.route('/setup/1', methods=['POST'])
        def setup1():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 400

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400
            
            setup_json = request.get_json()

            # Part 1: Check SQL Credentials
            try:
                sql = models.mysql.mysql()
                sql.connect(setup_json['hostname'], setup_json['username'], setup_json['password'])
                exists = sql.check_db_exists(setup_json['database'])
                return jsonify({'message': 'Connection Successful', 'exists': exists}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 500

        @setup_blueprint.route('/setup/2', methods=['POST'])
        def setup2():
            # Protect api call once is already configured
            if not self.__setup_available():
                return jsonify({}), 400

            if not request.is_json:
                return jsonify({"message": "Missing JSON in request"}), 400
            
            setup_json = request.get_json()

            # Part 2: Build Meteor & Create User Admin Account
            sql = models.mysql.mysql()
            sql.connect(setup_json['sql']['hostname'], setup_json['sql']['username'], setup_json['sql']['password'])

            try:
                sql.execute('DROP DATABASE IF EXISTS {}'.format(setup_json['sql']['database']))
                sql.execute('CREATE DATABASE {}'.format(setup_json['sql']['database']))
                sql.select_database(setup_json['sql']['database'])
                print("- Building SQL Schema in '{}' database ...".format(setup_json['sql']['database']))

                with open('{}/models/schema.sql'.format(self._ROOT_PATH)) as file_open:
                    queries = file_open.read().split(';')
                    for q in queries:
                        if q != '':
                            sql.execute(q)

                # Create user
                users = models.admin.users.Users(sql)
                user = {"username": setup_json['account']['username'], "password": setup_json['account']['password'], "email": "admin@admin.com", "coins": 100, "group": 'Administrator', "admin": 1}
                user['password'] = bcrypt.hashpw(user['password'].encode('utf8'), bcrypt.gensalt())
                users.post(user)

            except Exception as e:
                return jsonify({'message': str(e)}), 500

            # Write setup to the setup file
            setup_content = {
                "bind": "0.0.0.0:5000",
                "sql":
                {
                    "hostname": setup_json['sql']['hostname'],
                    "username": setup_json['sql']['username'],
                    "password": setup_json['sql']['password'],
                    "port": setup_json['sql']['port'],
                    "database": setup_json['sql']['database']
                }
            }
            with open(self._setup_file, 'w') as outfile:
                json.dump(setup_content, outfile)

            return jsonify({'message': 'Setup Finished Successfully'}), 200

        return setup_blueprint

    def __setup_available(self):
        if not os.path.exists(self._setup_file):
            return False
        with open(self._setup_file) as file_open:
            f = json.load(file_open)
            if f['sql']['hostname'] != '' or f['sql']['username'] != '' or f['sql']['password'] != '' or f['sql']['port'] != '' or f['sql']['database'] != '':
                return False
        return True
