from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
import json

import connectors.base
import models.admin.users
import models.inventory.auxiliary
import models.inventory.regions

class Auxiliary:
    def __init__(self, app, sql, license):
        self._app = app
        self._license = license
        # Init models
        self._users = models.admin.users.Users(sql)
        self._auxiliary = models.inventory.auxiliary.Auxiliary(sql, license)
        self._regions = models.inventory.regions.Regions(sql)

    def blueprint(self):
        # Init blueprint
        auxiliary_blueprint = Blueprint('auxiliary', __name__, template_folder='auxiliary')

        @auxiliary_blueprint.route('/inventory/auxiliary', methods=['GET','POST','PUT','DELETE'])
        @jwt_required()
        def auxiliary_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            auxiliary = request.get_json()

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user)
            elif request.method == 'POST':
                return self.post(user, auxiliary)
            elif request.method == 'PUT':
                return self.put(user, auxiliary)
            elif request.method == 'DELETE':
                return self.delete(user)

        @auxiliary_blueprint.route('/inventory/auxiliary/test', methods=['POST'])
        @jwt_required()
        def auxiliary_test_method():
            # Check license
            if not self._license.validated:
                return jsonify({"message": self._license.status['response']}), 401

            # Get User
            user = self._users.get(get_jwt_identity())[0]

            # Check user privileges
            if user['disabled'] or not user['inventory_enabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Get Request Json
            auxiliary_json = request.get_json()

            # Get region info
            region = self._regions.get(user_id=user['id'], group_id=user['group_id'], region_id=auxiliary_json['region'])
            if len(region) == 0:
                return jsonify({'message': "Can't test the connection. Invalid region provided."}), 400
            ssh = {'enabled': region[0]['ssh_tunnel'], 'hostname': region[0]['hostname'], 'port': region[0]['port'], 'username': region[0]['username'], 'password': region[0]['password'], 'key': region[0]['key']}

            # Build Auxiliary Data
            if 'auxiliary' in auxiliary_json:
                aux = self._auxiliary.get(user['id'], user['group_id'], auxiliary_json['auxiliary'])
                if len(aux) == 0:
                    return jsonify({'message': "Can't test the connection. Invalid auxiliary provided."}), 400
                sql = {"engine": aux[0]['engine'], "hostname": aux[0]['hostname'], "port": aux[0]['port'], "username": aux[0]['username'], "password": aux[0]['password'], 'ssl': aux[0]['ssl'], 'ssl_client_key': aux[0]['ssl_client_key'], 'ssl_client_certificate': aux[0]['ssl_client_certificate'], 'ssl_ca_certificate': aux[0]['ssl_ca_certificate'], 'ssl_verify_ca': aux[0]['ssl_verify_ca']}
            else:
                sql = {"engine": auxiliary_json['engine'], "hostname": auxiliary_json['hostname'], "port": auxiliary_json['port'], "username": auxiliary_json['username'], "password": auxiliary_json['password'], "ssl": auxiliary_json['ssl'], "ssl_client_key": auxiliary_json['ssl_client_key'], "ssl_client_certificate": auxiliary_json['ssl_client_certificate'], "ssl_ca_certificate": auxiliary_json['ssl_ca_certificate'], 'ssl_verify_ca': auxiliary_json['ssl_verify_ca']}
                if 'id' in auxiliary_json:
                    auxiliary_origin = self._auxiliary.get(user['id'], user['group_id'], auxiliary_json['id'])
                    sql['ssl_client_key'] = auxiliary_origin[0]['ssl_client_key'] if sql['ssl_client_key'] == '<ssl_client_key>' else sql['ssl_client_key']
                    sql['ssl_client_certificate'] = auxiliary_origin[0]['ssl_client_certificate'] if sql['ssl_client_certificate'] == '<ssl_client_certificate>' else sql['ssl_client_certificate']
                    sql['ssl_ca_certificate'] = auxiliary_origin[0]['ssl_ca_certificate'] if sql['ssl_ca_certificate'] == '<ssl_ca_certificate>' else sql['ssl_ca_certificate']

            # Check SQL Connection
            try:
                sql = connectors.base.Base({'ssh': ssh, 'sql': sql})
                sql.test_sql()
            except Exception as e:
                return jsonify({'message': str(e)}), 400

            return jsonify({'message': 'Connection Successful'}), 200

        return auxiliary_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user):
        # Get auxiliary
        auxiliary = self._auxiliary.get(user['id'], user['group_id'])
        # Protect SSL Keys
        for aux in auxiliary:
            aux['ssl_client_key'] = '<ssl_client_key>' if aux['ssl_client_key'] is not None else None
            aux['ssl_client_certificate'] = '<ssl_client_certificate>' if aux['ssl_client_certificate'] is not None else None
            aux['ssl_ca_certificate'] = '<ssl_ca_certificate>' if aux['ssl_ca_certificate'] is not None else None
        # Check Inventory Secured
        if user['inventory_secured'] and not user['owner']:
            auxiliary_secured = []
            for a in auxiliary:
                if a['shared']:
                    auxiliary_secured.append({"id": a['id'], "name": a['name'], "engine": a['engine'], "version": a['version'], "shared": a['shared'], "active": a['active']})
                else:
                    auxiliary_secured.append(a)
            return jsonify({'data': auxiliary_secured}), 200
        return jsonify({'data': auxiliary}), 200

    def post(self, user, auxiliary):
        # Check privileges
        if auxiliary['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check auxiliary exists
        if self._auxiliary.exist(user['id'], user['group_id'], auxiliary):
            return jsonify({'message': 'This auxiliary name currently exists'}), 400
        # Parse ssl
        if auxiliary['ssl'] and (auxiliary['ssl_client_key'] == '<ssl_client_key>' or auxiliary['ssl_client_certificate'] == '<ssl_client_certificate>' or auxiliary['ssl_ca_certificate'] == '<ssl_ca_certificate>'):
            origin = self._auxiliary.get(user['id'], user['group_id'], auxiliary['id'])[0]
            auxiliary['ssl_client_key'] = origin['ssl_client_key'] if auxiliary['ssl_client_key'] == '<ssl_client_key>' else auxiliary['ssl_client_key']
            auxiliary['ssl_client_certificate'] = origin['ssl_client_certificate'] if auxiliary['ssl_client_certificate'] == '<ssl_client_certificate>' else auxiliary['ssl_client_certificate']
            auxiliary['ssl_ca_certificate'] = origin['ssl_ca_certificate'] if auxiliary['ssl_ca_certificate'] == '<ssl_ca_certificate>' else auxiliary['ssl_ca_certificate']
        # Add auxiliary
        self._auxiliary.post(user['id'], user['group_id'], auxiliary)
        return jsonify({'message': 'Auxiliary connection added successfully'}), 200

    def put(self, user, auxiliary):
        # Check privileges
        if auxiliary['shared'] and not user['owner']:
            return jsonify({'message': "Insufficient privileges"}), 401
        # Check auxiliary exists
        if self._auxiliary.exist(user['id'], user['group_id'], auxiliary):
            return jsonify({'message': 'This auxiliary name currently exists'}), 400
        # Edit auxiliary
        self._auxiliary.put(user['id'], user['group_id'], auxiliary)
        return jsonify({'message': 'Auxiliary connection edited successfully'}), 200

    def delete(self, user):
        data = json.loads(request.args['auxiliary'])
        # Check privileges
        for auxiliary in data:
            auxiliary = self._auxiliary.get(user['id'], user['group_id'], auxiliary)
            if len(auxiliary) > 0 and auxiliary[0]['shared'] and not user['owner']:
                return jsonify({'message': "Insufficient privileges"}), 401
        # Delete auxiliary
        for auxiliary in data:
            self._auxiliary.delete(user['id'], user['group_id'], auxiliary)
        return jsonify({'message': 'Selected auxiliary connections deleted successfully'}), 200
