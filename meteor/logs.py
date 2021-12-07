import json

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
            with open(f"{self._args.path}/../{self._args.uri}.json", 'w') as outfile:
                json.dump(file, outfile, separators=(',', ':'))

        except Exception as e:
            raise Exception('An error occurred compiling logs. ' + str(e))
