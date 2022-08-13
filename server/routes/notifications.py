from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)
from sentry_sdk import set_user

import models.admin.users
import models.notifications

class Notifications:
    def __init__(self, license):
        self._license = license

    def init(self, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._notifications = models.notifications.Notifications(sql)

    def blueprint(self):
        # Init blueprint
        notifications_blueprint = Blueprint('notifications', __name__, template_folder='notifications')

        @notifications_blueprint.route('/notifications', methods=['GET','PUT','DELETE'])
        @jwt_required()
        def notifications_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            if request.method == 'GET':
                return self.get(user['id'])
            elif request.method == 'PUT':
                return self.put(user['id'])
            elif request.method == 'DELETE':
                return self.delete(user['id'])

        @notifications_blueprint.route('/notifications/bar', methods=['GET'])
        @jwt_required()
        def notifications_bar_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401

            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Update user last ping
            self._users.put_last_ping(user['id'])

            # Return unseen user notifications
            return jsonify({'data': self._notifications.get_notification_bar(user['id'])}), 200
    
        @notifications_blueprint.route('/notifications/clear', methods=['DELETE'])
        @jwt_required()
        def notifications_clear_method():
            # Check license
            if not self._license.is_validated():
                return jsonify({"message": self._license.get_status()['response']}), 401
            
            # Get user data
            try:
                user = self._users.get(get_jwt_identity())[0]
                set_user({"id": user['id'], "username": user['username'], "email": user['email']})
            except IndexError:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Check user privileges
            if user['disabled']:
                return jsonify({'message': 'Insufficient Privileges'}), 401

            # Clear all notifications
            self._notifications.clear(user['id'])

            return jsonify({'message': 'All notifications have been cleared'}), 200

        return notifications_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user_id):
        return jsonify({'data': self._notifications.get(user_id)}), 200

    def put(self, user_id):
        data = request.get_json()
        self._notifications.put(user_id, data)
        return jsonify({'message': 'Notification edited'}), 200

    def delete(self, user_id):
        # Check inconsistencies
        data = request.get_json()
        for notification in data:
            self._notifications.delete(user_id, notification)
        return jsonify({'message': 'Selected notifications deleted'}), 200
