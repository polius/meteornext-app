from flask import Blueprint
import imp
import os

def construct_blueprint(credentials):
    models_path = '{}/../models'.format(os.path.dirname(os.path.abspath(__file__)))
    deployments_storage = imp.load_source('deployments', '{}/deployments.py'.format(models_path))
    deployments_storage.Deployments()

    deployments = Blueprint('deployments', __name__, template_folder='deployments')

    @deployments.route('/deployments', methods=['GET', 'POST'])
    def get_deployments():
        response_object = {'status': 'success'}
        if request.method == 'POST':
            post_data = request.get_json()
            BOOKS.append({
                'id': uuid.uuid4().hex,
                'title': post_data.get('title'),
                'author': post_data.get('author'),
                'read': post_data.get('read')
            })
            response_object['message'] = 'Book added!'
        else:
            # response_object['books'] = BOOKS
            response_object = {'items': 'PRODUCTION'}
        return jsonify(response_object)


    @deployments.route('/deployments/<deployment_id>', methods=['PUT', 'DELETE'])
    def get_deployment(book_id):
        response_object = {'status': 'success'}
        if request.method == 'PUT':
            post_data = request.get_json()
            remove_book(book_id)
            BOOKS.append({
                'id': uuid.uuid4().hex,
                'title': post_data.get('title'),
                'author': post_data.get('author'),
                'read': post_data.get('read')
            })
            response_object['message'] = 'Book updated!'
        if request.method == 'DELETE':
            remove_book(book_id)
            response_object['message'] = 'Book removed!'
        return jsonify(response_object)

    def remove_deployments(book_id):
        for book in BOOKS:
            if book['id'] == book_id:
                BOOKS.remove(book)
                return True
        return False

    return deployments