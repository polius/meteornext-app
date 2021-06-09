import sys
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import routes.license
import models.mysql

# Get Credentials File
with open('licenser.conf') as json_file:
    data = json.load(json_file)

# Instantiate SQL Class & Connect
sql = models.mysql.mysql()
try:
    sql.connect(data['hostname'], data['username'], data['password'], data['port'], data['database'])
except Exception as e:
    print("- Invalid SQL Credentials")
    print('- Error: {}'.format(e))
    sys.exit()

# Instantiate Flask App
app = Flask(__name__)
app.config.from_object(__name__)

# Instantiate & Register Settings Blueprint
l = routes.license.License(sql)
app.register_blueprint(l.blueprint())

# Enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# Run with python
if __name__ == '__main__':
    app.run(host='127.0.0.1', port='5000', debug=True)