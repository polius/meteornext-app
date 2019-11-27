# -*- coding: utf-8 -*-
import os
import sys
import json
import uuid
import datetime
import argparse
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from cron import Cron
import routes.login
import routes.profile
import routes.admin.settings
import routes.admin.groups
import routes.admin.users
import routes.admin.deployments
import routes.deployments.settings.environments
import routes.deployments.settings.regions
import routes.deployments.settings.servers
import routes.deployments.settings.auxiliary
import routes.deployments.settings.slack
import routes.deployments.deployments
import routes.deployments.views.basic
import routes.deployments.views.pro
import models.mysql

DIR_PATH = os.path.dirname(os.path.realpath(__file__)) if sys.argv[0].endswith('.py') else os.path.dirname(sys.executable)
EXE_PATH = os.path.dirname(os.path.realpath(__file__))

def config(args):
    if not os.path.isfile("{}/settings.json".format(DIR_PATH)) and not args.config:
        print("Please run: './server --config' to initialize all settings")
        sys.exit()

    try:
        with open("{}/settings.json".format(DIR_PATH)) as file_open:
            settings = json.load(file_open)
    except Exception:
        settings = {"bind": '', "sql": {"hostname": '', "username": '', "password": '', "port": '', "database": ''}}
    
    if args.config:
        config = {}
        bind = "[0.0.0.0:5000]" if settings['bind'] == '' else '[' + settings['bind'] + ']'
        config['bind'] = raw_input("- Enter the server bind address {}: ".format(bind))
        settings['bind'] = config['bind'] if config['bind'] != '' else '0.0.0.0:5000' if settings['bind'] == '' else settings['bind']
        hostname = ' [' + settings['sql']['hostname'] + ']' if settings['sql']['hostname'] != '' else ''
        username = ' [' + settings['sql']['username'] + ']' if settings['sql']['username'] != '' else ''
        password = ' [' + settings['sql']['password'] + ']' if settings['sql']['password'] != '' else ''
        port = ' [' + settings['sql']['port'] + ']' if settings['sql']['port'] != '' else ' [3306]'
        database = ' [' + settings['sql']['database'] + ']' if settings['sql']['database'] != '' else ' [meteor]'
        config['sql'] = {
            "hostname": raw_input("- Enter the SQL hostname{}: ".format(hostname)),
            "username": raw_input("- Enter the SQL username{}: ".format(username)),
            "password": raw_input("- Enter the SQL password{}: ".format(password)),
            "port": raw_input("- Enter the SQL port{}: ".format(port)),
            "database": raw_input("- Enter the SQL database{}: ".format(database))
        }
        settings['sql']['hostname'] = config['sql']['hostname'] if config['sql']['hostname'] != '' else settings['sql']['hostname']
        settings['sql']['username'] = config['sql']['username'] if config['sql']['username'] != '' else settings['sql']['username']
        settings['sql']['password'] = config['sql']['password'] if config['sql']['password'] != '' else settings['sql']['password']
        settings['sql']['port'] = config['sql']['port'] if config['sql']['port'] != '' else '3306' if settings['sql']['port'] == '' else settings['sql']['port']
        settings['sql']['database'] = config['sql']['database'] if config['sql']['database'] != '' else 'meteor' if settings['sql']['database'] == '' else settings['sql']['database']

    # Check SQL Connection
    try:
        sql = models.mysql.mysql()
        sql.connect(settings['sql']['hostname'], settings['sql']['username'], settings['sql']['password'], settings['sql']['database'])
    except Exception as e:
        print("--> SQL Connection failed. Please check the entered SQL credentials.")
        sys.exit()

    if args.config:
        # Check SQL Database
        if sql.check_db_exists(settings['sql']['database']):
            print("--> A database named '{}' has been detected in '{}'.".format(settings['sql']['database'], settings['sql']['hostname']))
            confirm = raw_input("- Do you want to recreate the database '{}'? (y/n): ",format(settings['sql']['database']))
            if confirm == 'y':
                sql.execute('DROP DATABASE {}'.format(settings['sql']['database']))
                sql.execute('CREATE DATABASE {}'.format(settings['sql']['database']))
                print("--> Building SQL Schema in '{}' database ...".format(settings['sql']['database']))
                sql.execute('CREATE DATABASE {}'.format(settings['sql']['database']))
                with open('{}/models/schema.sql'.format(EXE_PATH)) as file_open:
                    queries = file_open.read().split(';')
                    for q in queries:
                        if q != '':
                            sql.execute(q, settings['sql']['database'])

        # Store Credentials
        with open("{}/settings.json".format(DIR_PATH), 'w') as outfile:
            json.dump(settings, outfile)
        print("--> Configuration stored successfully in '{}/settings.json'.".format(DIR_PATH))
        sys.exit()

    if settings['bind'] == '' or settings['sql']['hostname'] == '' or settings['sql']['username'] == '' or settings['sql']['password'] == '' or settings['sql']['port'] == '' or settings['sql']['database'] == '':
        print("Some configuration fields are empty. Please use: './server --config' and fill all fields accordingly.")
        sys.exit()

    return {"settings": settings, "sql": sql}

# Start Parser
parser = argparse.ArgumentParser(description='Meteor Next Server')
parser.add_argument('--config', required=False, action='store_true', dest='config', help='Configure required Meteor Next settings')
args = parser.parse_args()

# Instantiate Flask App
app = Flask(__name__)
app.config.from_object(__name__)
app.config['JWT_SECRET_KEY'] = '1T20PQAsDE37efH4APvJpgaV1rJse7bkl8+BfoSTLSM='  # Using Docker: os.environ.get('SECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=8)  # days = 1
jwt = JWTManager(app)

# Load SQL Configuration
config = config(args)
settings = config['settings']
sql = config['sql']

# Init all blueprints
login = routes.login.Login(sql).blueprint()
profile = routes.profile.Profile(sql).blueprint()
settings = routes.admin.settings.Settings(settings, sql).blueprint()
groups = routes.admin.groups.Groups(sql).blueprint()
users = routes.admin.users.Users(sql).blueprint()
admin_deployments = routes.admin.deployments.Deployments(sql).blueprint()
environments = routes.deployments.settings.environments.Environments(sql).blueprint()
regions = routes.deployments.settings.regions.Regions(sql).blueprint()
servers = routes.deployments.settings.servers.Servers(sql).blueprint()
auxiliary = routes.deployments.settings.auxiliary.Auxiliary(sql).blueprint()
slack = routes.deployments.settings.slack.Slack(sql).blueprint()
deployments = routes.deployments.deployments.Deployments(sql).blueprint()
deployments_basic = routes.deployments.views.basic.Basic(sql).blueprint()
deployments_pro = routes.deployments.views.pro.Pro(sql).blueprint()

# Instantiate all routes
app.register_blueprint(login)
app.register_blueprint(profile)
app.register_blueprint(settings)
app.register_blueprint(groups)
app.register_blueprint(users)
app.register_blueprint(admin_deployments)
app.register_blueprint(environments)
app.register_blueprint(regions)
app.register_blueprint(servers)
app.register_blueprint(auxiliary)
app.register_blueprint(slack)
app.register_blueprint(deployments)
app.register_blueprint(deployments_basic)
app.register_blueprint(deployments_pro)

# Enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

# Start cron
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    Cron(sql)

# DEBUG
if __name__ == '__main__':
    host = settings['bind'][:settings['bind'].find(':')]
    port = settings['bind'][settings['bind'].find(':')+1:]
    app.run(host=host, port=port)
