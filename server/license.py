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
        if self._license_params.get('access_key') == 'meteornext' and self._license_params.get('secret_key') == 'meteornext':
            self._license_status = {"code": 200, "response": "The license is valid.", "account": "License GPLv3", "resources": -1, "sentry": False}
        else:
            self._license_status = {"code": 401, "response": "Use 'meteornext' for both Api Key and Secret Key.", "account": None, "resources": None, "sentry": False}
