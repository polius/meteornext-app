import os
import json
import shutil

class logs:
    def __init__(self, args):
        self._args = args

    def compile(self, logs, summary_raw, exception=None):
        try:
            with open("{}/meteor.js".format(self._args.path), 'w') as write_file:
                # Write Parsed Data
                write_file.write('var DATA = {};\n'.format(json.dumps(logs, separators=(',', ':'))))
                # Write Sorted Displayed Columns
                write_file.write('var COLUMNS = ["meteor_timestamp", "meteor_environment", "meteor_region", "meteor_server", "meteor_database", "meteor_query", "meteor_status", "meteor_response", "meteor_execution_time", "meteor_execution_rows", "meteor_output"];\n')
                # Write the Execution Information
                summary = summary_raw
                summary['mode'] = 'deploy' if self._args.deploy else 'test' 
                write_file.write('var INFO = {};\n'.format(json.dumps(summary, separators=(',', ':'))))
                # If there's an Exception, add it to the file
                if exception is not None and not exception.startswith('[QUERY_ERROR]'):
                    parsed_exception = exception.replace('"', '\\"').replace("\n", "\\n")
                    write_file.write('var ERROR = "{}";\n'.format(parsed_exception))

            # Compress Logs
            self.__compress()
            
        except Exception as e:
            raise Exception('[USER] Error Compiling Meteor Data. ' + str(e))

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
