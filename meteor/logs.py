import json

class logs:
    def __init__(self, args, imports, progress):
        self._args = args
        self._imports = imports
        self._progress = progress

    def compile(self, logs, summary, error=None):
        try:
            # Generate file
            summary['mode'] = 'deploy' if self._args.deploy else 'test'
            file = {"DATA": logs, "COLUMNS": ["meteor_timestamp", "meteor_environment", "meteor_region", "meteor_server", "meteor_database", "meteor_query", "meteor_status", "meteor_response", "meteor_execution_time", "meteor_execution_rows", "meteor_output"], "INFO": summary}
            if error:
                file['ERROR'] = str(error)

            # Save file
            file_path = f"{self._args.path}/{self._args.uri}.json" if self._imports.config['amazon_s3']['enabled'] else f"{self._args.path}/../{self._args.uri}.json"
            with open(file_path, 'w') as outfile:
                json.dump(file, outfile, separators=(',', ':'))

            self._progress.track_logs(value={'status': 'success'})

        except Exception:
            self._progress.track_logs(value={'status': 'failed'})
            raise

