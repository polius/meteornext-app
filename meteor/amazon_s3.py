import boto3

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

    def upload_logs(self):
        # Upload Logs to S3
        if self._config['amazon_s3']['enabled']:
            # print("+==================================================================+")
            # print("|  AMAZON S3                                                       |")
            # print("+==================================================================+")
            try:
                # Upload Logs to S3
                status_msg = "- Uploading Logs to S3 Bucket '{}'".format(self._config['amazon_s3']['bucket_name'])
                # print(status_msg)
                self._progress.track_tasks(value={'status': 'progress', 'message': "Uploading Logs to Amazon S3..."})
                execution_name = self._args.path[self._args.path.rfind('/')+1:]

                # 1. Upload Compressed Logs Folder to '/logs'
                file_path = "{}.tar.gz".format(self._args.path)
                bucket_name = self._config['amazon_s3']['bucket_name']
                s3_path = "logs/{}.tar.gz".format(execution_name)
                self._amazon_s3.meta.client.upload_file(file_path, bucket_name, s3_path)

                # 2. Upload Results File to '/results'
                file_path = "{}/meteor.js".format(self._args.path)
                s3_path = "results/{}.js".format(execution_name)
                self._amazon_s3.meta.client.upload_file(file_path, bucket_name, s3_path)

            except Exception as e:
                # print("- Uploading Process Failed.")
                self._progress.track_tasks(value={'status': 'false'})
                raise
            else:
                self._progress.track_tasks(value={'status': 'success'})