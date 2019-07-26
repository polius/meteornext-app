from flask import request, jsonify, Blueprint
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required, get_jwt_identity)

login = Blueprint('login', __name__, template_folder='login')

@login.route('/login', methods=['POST'])
def login_user():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if username != 'test' and password != 'test':
        return jsonify({'status': False, "message": "Bad username or password."}), 401
    # if username == '' and flask_bcrypt.check_password_hash(password) == '':
    #     return jsonify({'ok': False, "message": "Bad username or password"}), 401

    # Use create_access_token() and create_refresh_token() to create our
    # access and refresh tokens
    ret = {
        'access_token': create_access_token(identity=username),
        'refresh_token': create_refresh_token(identity=username),
        'is_admin': 1
    }
    return jsonify({'status': True, 'data': ret}), 200


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