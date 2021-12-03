import os
import gzip
import json
import shutil

class logs:
    def __init__(self, args, imports):
        self._args = args
        self._imports = imports

    def compile(self, logs, summary, exception=None):
        try:
            # Generate file
            summary['mode'] = 'deploy' if self._args.deploy else 'test'
            file = {"DATA": logs, "COLUMNS": ["meteor_timestamp", "meteor_environment", "meteor_region", "meteor_server", "meteor_database", "meteor_query", "meteor_status", "meteor_response", "meteor_execution_time", "meteor_execution_rows", "meteor_output"], "INFO": summary}
            if exception is not None and not exception.startswith('[QUERY_ERROR]'):
                file['ERROR'] = exception.replace('"', '\\"').replace("\n", "\\n")

            # Save file
            with open("{}/meteor.json".format(self._args.path), 'w') as outfile:
                json.dump(file, outfile, separators=(',', ':'))

            # Compress Logs
            self.__compress()
            
        except Exception as e:
            raise Exception('An error occurred compiling logs. ' + str(e))

    def __compress(self):
        # Delete temp file
        blueprint_pyc = "{}/blueprint.pyc".format(self._args.path)
        if os.path.exists(blueprint_pyc):
            os.remove(blueprint_pyc)

        pycache = "{}/__pycache__".format(self._args.path)
        if os.path.exists(pycache):
            shutil.rmtree(pycache)

        # Tar Gz Deploy Folder
        shutil.make_archive(self._args.path, 'gztar', self._args.path)

        # Compress Results (to upload it to S3)
        if self._imports.config['amazon_s3']['enabled']:
            with open(f"{self._args.path}/meteor.json", 'rb') as f_in:
                with gzip.open(f"{self._args.path}/meteor.json.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
