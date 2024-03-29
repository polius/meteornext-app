import os
import sys
import hashlib
import logging
import tarfile
import time
import datetime
import subprocess
import gunicorn.app.base
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_compress import Compress
from flask_jwt_extended import (JWTManager, jwt_required, get_jwt_identity)
from logging.handlers import RotatingFileHandler

class Api:
    def __init__(self, version, license, sentry_dsn, node):
        # Instantiate Flask App
        app = Flask(__name__)
        app.config.from_object(__name__)
        app.config['JSON_SORT_KEYS'] = False

        # Get unique hardware MAC address
        p = subprocess.Popen(["cat", "/sys/class/net/eth0/address"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # JWT Config
        app.config['JWT_SECRET_KEY'] = hashlib.md5(p.stdout.readlines()[0].strip()).hexdigest()
        app.secret_key = app.config['JWT_SECRET_KEY']
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=12)
        app.config['JWT_TOKEN_LOCATION'] = ['cookies']
        app.config['JWT_COOKIE_SECURE'] = 'SECURE' in os.environ and os.environ['SECURE'] == 'True'
        app.config['JWT_COOKIE_SAMESITE'] = 'Strict'
        JWTManager(app)

        # Compress Flask application's responses with gzip, deflate or brotli
        Compress(app)

        # Instantiate & Register Settings Blueprint
        URL_PREFIX = "/api"
        import routes.setup
        routes.setup.Setup(app, version, license, URL_PREFIX, sentry_dsn)

        # Enable CORS
        CORS(app)

        # Health endpoint
        @app.route("/api/health")
        def health_method():
            return ''

        # Metadata endpoint
        @app.route("/api/metadata")
        def metadata_method():
            try:
                return jsonify({'enabled': license.is_validated(), 'resources': license.get_resources(), 'sentry': license.get_status().get('sentry', False), 'node': node})
            except BrokenPipeError:
                return jsonify({'enabled': False, 'resources': 1, 'sentry': False, 'node': node})

        # Version endpoint
        @app.route('/api/version', methods=['GET'])
        @jwt_required()
        def version_method():
            return jsonify({'version': version})

        # Log requests
        handler = RotatingFileHandler('server.log', maxBytes=10485760, backupCount=1)
        logger = logging.getLogger('accesslog')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        @app.after_request
        @jwt_required(optional=True)
        def after_request(response):
            exceptions = ['/api/metadata']
            if request.full_path[:-1] not in exceptions:
                timestamp = time.strftime('[%Y-%b-%d %H:%M:%S]')
                ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0] if request.headers.getlist("X-Forwarded-For") else request.remote_addr
                logger.info('%s %s %s %s %s %s %s', timestamp, get_jwt_identity(), ip, request.method, request.scheme, request.full_path[:-1], response.status)
            return response

        # Init gunicorn vars
        MAX_THREADS = 1000000
        try:
            THREADS = int(os.environ['MAX_REQUESTS']) if 'MAX_REQUESTS' in os.environ else 1000
            if THREADS < 1:
                THREADS = 1
            elif THREADS > MAX_THREADS:
                THREADS = MAX_THREADS
        except Exception:
            THREADS = 1000
            # print("- The 'MAX_REQUESTS' parameter is invalid.")
        # finally:
            # print(f"- Max Concurrent Requests: {THREADS}")

        # Start Api
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Extract Meteor
            with tarfile.open(f"{sys._MEIPASS}/apps/meteor.tar.gz") as tar:
                tar.extractall(path=f"{sys._MEIPASS}/apps/meteor/")
            StandaloneApplication(app, {"worker_class": "gthread", "threads": THREADS, "worker_connections": MAX_THREADS+1, "bind": "unix:server.sock", "pidfile": "server.pid", "timeout": 3600, "capture_output": True, "errorlog": "server.err"}).run()
        else:
            # StandaloneApplication(app, {"worker_class": "gthread", "threads": THREADS, "worker_connections": MAX_THREADS+1, "bind": "0.0.0.0:5000", "pidfile": "server.pid", "timeout": 3600}).run()
            StandaloneApplication(app, {"worker_class": "gthread", "threads": THREADS, "worker_connections": MAX_THREADS+1, "bind": "unix:server.sock", "pidfile": "server.pid", "timeout": 3600, "capture_output": True, "errorlog": "server.err"}).run()

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()
    def load_config(self):
        config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)
    def load(self):
        return self.application
