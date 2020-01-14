from flask import Blueprint, jsonify, request
from flask_jwt_extended import (jwt_required, get_jwt_identity)

import models.admin.users
import models.notifications

class Notifications:
    def __init__(self, app, sql):
        # Init models
        self._users = models.admin.users.Users(sql)
        self._notifications = models.notifications.Notifications(sql)

    def license(self, value):
        self._license = value

    def blueprint(self):
        # Init blueprint
        notifications_blueprint = Blueprint('notifications', __name__, template_folder='notifications')

        @notifications_blueprint.route('/notifications', methods=['GET','PUT','DELETE'])
        @jwt_required
        def notifications_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401

            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Get Request Json
            notifications_json = request.get_json()

            if request.method == 'GET':
                return self.get(user['id'])
            elif request.method == 'PUT':
                return self.put(user['id'], notifications_json)
            elif request.method == 'DELETE':
                return self.delete(user['id'], notifications_json)

        @notifications_blueprint.route('/notifications/bar', methods=['GET'])
        @jwt_required
        def notifications_unseen_method():
            # Check license
            if not self._license['status']:
                return jsonify({"message": self._license['response']}), 401
            
            # Get user data
            user = self._users.get(get_jwt_identity())[0]

            # Return unseen user notifications
            return jsonify({'data': self._notifications.get_notification_bar(user['id'])}), 200

        return notifications_blueprint

    ####################
    # Internal Methods #
    ####################
    def get(self, user_id):
        return jsonify({'data': self._notifications.get(user_id)}), 200

    def put(self, user_id, data):
        self._notifications.put(user_id, data)
        return jsonify({'message': 'Notification edited successfully'}), 200

    def delete(self, user_id, data):
        # Check inconsistencies
        for notification in data:
            self._notifications.delete(user_id, notification)
        return jsonify({'message': 'Selected notifications deleted successfully'}), 200
