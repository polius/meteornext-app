import uuid
import json
import hashlib
from datetime import datetime

class License:
    def __init__(self, version):
        self._version = version
        self._license_params = None
        self._license_status = {}
        self._last_check_date = datetime.utcnow()

    def get_status(self):
        return self._license_status

    def is_validated(self):
        return self._license_status and self._license_status['code'] == 200

    def get_resources(self):
        return self._license_status.get('resources')

    def get_last_check_date(self):
        return self._last_check_date

    def set_license(self, license):
        self._license_params = license

    def validate(self, force=False):
        if force or not self._license_status or self._license_status['code'] != 200:
            # Check license
            self.__check()

            # Store last check date
            self._last_check_date = datetime.utcnow()

    def __check(self):
        try:
            # Import requests lib
            import requests

            # Add version
            self._license_params['version'] = self._version

            # Generate challenge
            self._license_params['challenge'] = str(uuid.uuid4())

            # Check license
            response = requests.post("https://license.meteornext.io/", json=self._license_params, headers={"x-meteor2-key": self._license_params['access_key']}, allow_redirects=False)

            # Check "x-meteor2-key" header is valid
            if response.status_code != 200:
                self._license_status = {"code": response.status_code, "response": "The license is not valid.", "account": None, "resources": None, "sentry": None}
            else:
                # Check license is valid
                response_code = json.loads(response.text)['statusCode']
                response_body = json.loads(response.text)['body']
                response_text = response_body['response']
                account = response_body['account'] if response_code == 200 else None
                resources = response_body['resources'] if response_code == 200 else None
                sentry = response_body['sentry'] if response_code == 200 else False

                # Solve challenge
                if response_code == 200:
                    response_challenge = response_body['challenge']
                    challenge = ','.join([str(ord(i)) for i in self._license_params['challenge']])
                    challenge = hashlib.sha3_256(challenge.encode()).hexdigest()

                    # Validate challenge
                    if response_challenge != challenge:
                        response_text = "The license is not valid."
                        response_code = 401

                self._license_status = {"code": response_code, "response": response_text, "account": account, "resources": resources, "sentry": sentry}
        except Exception:
            if not self._license_status or self._license_status['code'] != 200 or int((datetime.utcnow()-self._last_check_date).total_seconds()) > 3600:
                self._license_status = {"code": 404, "response": "A connection to the licensing server could not be established"}
