import uuid
from flask import Flask, jsonify, request
from flask_cors import CORS
from routes.deployments import deployments

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# instantiate all routes
app.register_blueprint(deployments)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')

if __name__ == '__main__':
    app.run(host='0.0.0.0')