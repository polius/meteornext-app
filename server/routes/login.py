import imp
import bcrypt
from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

def construct_blueprint(credentials):
    # Init blueprint
    login = Blueprint('login', __name__, template_folder='login')

    # Init models
    users = imp.load_source('users', '{}/models/admin/users.py'.format(credentials['path'])).Users(credentials)

    @login.route('/login', methods=['POST'])
    def login_user():
        if not request.is_json:
            return jsonify({"message": "Missing JSON in request"}), 400

        data = request.get_json()
        
        # Get User from Database
        user = users.get(data['username'])

        if len(user) == 0 or not bcrypt.checkpw(data['password'].encode('utf8'), user[0]['password'].encode('utf8')):
            return jsonify({"msg": "Invalid username and password."}), 401
        else:
            ret = {
                'access_token': create_access_token(identity=user[0]['username']),
                'refresh_token': create_refresh_token(identity=user[0]['username']),
                'username': user[0]['username'],
                'admin': user[0]['admin']
            }
            return jsonify({'data': ret}), 200

    # @login.route('/register', methods=['POST'])
    # def register():
    #     ''' register user endpoint '''
    #     data = validate_user(request.get_json())
    #     if data['ok']:
    #         data = data['data']
    #         data['password'] = flask_bcrypt.generate_password_hash(data['password'])
    #         mongo.db.users.insert_one(data)
    #         return jsonify({'ok': True, 'message': 'User created successfully!'}), 200
    #     else:
    #         return jsonify({'ok': False, 'message': 'Bad request parameters: {}'.format(data['message'])}), 400


    @login.route('/refresh', methods=['POST'])
    @jwt_refresh_token_required
    def refresh():
        ''' refresh token endpoint '''
        current_user = get_jwt_identity()
        ret = {
            'token': create_access_token(identity=current_user)
        }
        return jsonify({'status': True, 'data': ret}), 200


    @login.route('/protected', methods=['GET'])
    @jwt_required
    def protected():
        username = get_jwt_identity()
        return jsonify(logged_in_as=username), 200


    # @app.route('/user', methods=['GET', 'DELETE', 'PATCH'])
    # @jwt_required
    # def user():
    #     ''' route read user '''
    #     if request.method == 'GET':
    #         query = request.args
    #         data = mongo.db.users.find_one(query, {"_id": 0})
    #         return jsonify({'ok': True, 'data': data}), 200

    #     data = request.json()
    #     if request.method == 'DELETE':
    #         if data.get('email', None) is not None:
    #             db_response = mongo.db.users.delete_one({'email': data['email']})
    #             if db_response.deleted_count == 1:
    #                 response = {'ok': True, 'message': 'record deleted'}
    #             else:
    #                 response = {'ok': True, 'message': 'no record found'}
    #             return jsonify(response), 200
    #         else:
    #             return jsonify({'ok': False, 'message': 'Bad request parameters!'}), 400

    #     if request.method == 'PATCH':
    #         if data.get('query', {}) != {}:
    #             mongo.db.users.update_one(
    #                 data['query'], {'$set': data.get('payload', {})})
    #             return jsonify({'ok': True, 'message': 'record updated'}), 200
    #         else:
    #             return jsonify({'ok': False, 'message': 'Bad request parameters!'}), 400
    return login