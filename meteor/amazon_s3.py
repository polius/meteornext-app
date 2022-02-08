import gzip
import boto3
import shutil

class amazon_s3:
    def __init__(self, args, imports, progress):
        self._args = args
        self._config = imports.config
        self._progress = progress

        if self._config['amazon_s3']['enabled']:
            session = boto3.Session(
                aws_access_key_id=self._config['amazon_s3']['aws_access_key_id'],
                aws_secret_access_key=self._config['amazon_s3']['aws_secret_access_key'],
                region_name=self._config['amazon_s3']['region_name']
            )
            self._amazon_s3 = session.resource('s3')

    def upload(self):
        # Upload Logs to S3
        if self._config['amazon_s3']['enabled']:
            try:
                self._progress.track_tasks(value={'status': 'progress', 'message': "Uploading Deployment to Amazon S3..."})
                # Compress Deployment
                with open(f"{self._args.path}/{self._args.uri}.json", 'rb') as f_in:
                    with gzip.open(f"{self._args.path}/{self._args.uri}.json.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Upload Deployment to S3
                file_path = f"{self._args.path}/{self._args.uri}.json.gz"
                bucket_name = self._config['amazon_s3']['bucket_name']
                s3_path = f"deployments/{self._args.uri}.json.gz"
                self._amazon_s3.meta.client.upload_file(file_path, bucket_name, s3_path)

                # Update Progress
                self._progress.track_tasks(value={'status': 'success'})
            except Exception:
                self._progress.track_tasks(value={'status': 'failed'})
                raise
