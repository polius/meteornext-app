# Signing AWS API requests (Signature Version 4)
from botocore.auth import S3SigV4QueryAuth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

class ApiSign:
    def __init__(self, access_key, secret_key, region, expires=60):
        self._credentials = Credentials(access_key, secret_key)
        self._region = region
        self._expires = expires

    def get_s3_object(self, bucket, file):
        service = 's3'
        method = 'GET'
        url = f'https://{bucket}.s3.{self._region}.amazonaws.com/{file}'
        return self.__sign(service, method, url)

    def __sign(self, service, method, url):
        request = AWSRequest(method=method, url=url)
        S3SigV4QueryAuth(self._credentials, service, self._region, self._expires).add_auth(request)
        return request.prepare().url
