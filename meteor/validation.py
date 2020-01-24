import os
import re
import time
import threading

from query import query
from validate_regions import validate_regions

class validation:
    def __init__(self, args, imports, progress):
        # Init vars
        self._args = args
        self._credentials = imports.credentials
        self._progress = progress
        self._query_execution = imports.query_execution
        self._time = None

        # Init classes
        self._query = query(self._args, imports)

    @property
    def time(self):
        return self._time

    def start(self):
        print("+==================================================================+")
        print("|  VALIDATION                                                      |")
        print("+==================================================================+")
        try:
            self._start_time = time.time()
            self.__validate_credentials()
            self.__validate_queries()
            self.__validate_regions()
        finally:
            self._time = time.time()
            
    def __validate_credentials(self):
        print("+------------------------------------------------------------------+")
        print("| Validating Credentials                                           |")
        print("+------------------------------------------------------------------+")
        # Check --environment exists
        if self._args.environment not in self._credentials['environments'].keys():
            raise Exception("The Environment '{}' does not exist.".format(self._args.environment))

        regions = self._credentials['environments'][self._args.environment]
        regions_list = []
        servers_list = []
        for region in regions:
            # Region
            if region['region'] == '':
                raise Exception("[Environment: {}] The Region can not be empty.".format(self._args.environment))
            elif region['region'] in regions_list:
                raise Exception("[Environment: {}] The Region should be unique. There are two regions named '{}'.".format(self._args.environment, region['region']))
            regions_list.append(region['region'])

            # SSH
            if region['ssh']['enabled'] and region['ssh']['hostname'] == '':
                raise Exception("[Environment: {}] The SSH hostname can not be empty.".format(self._args.environment))
            if region['ssh']['enabled'] and region['ssh']['key'] != '' and not os.path.isfile(region['ssh']['key']):
                raise Exception("[Environment: {}] The SSH key '{}' does not exist in the path provided.".format(self._args.environment, region['ssh']['key']))

            # SQL
            for sql in region['sql']:
                if sql['name'] == '':
                    raise Exception("[Environment: {}] The SQL name should be filled.".format(self._args.environment))
                if sql['hostname'] == '':
                    raise Exception("[Environment: {}] The SQL hostname should be filled.".format(self._args.environment))
                if sql['username'] == '':
                    raise Exception("[Environment: {}] The SQL username should be filled.".format(self._args.environment))

                # Add sql['name'] to the list
                servers_list.append(sql['name'])
            
            # Check if there are duplicated sql ids in all environment servers
            seen = set()
            seen_add = seen.add
            seen_twice = set( x for x in servers_list if x in seen or seen_add(x) )
            if len(seen_twice) > 0:
                raise Exception("[Environment: {}] The server name should be unique. There are two IDs named '{}'".format(self._args.environment, str(list(seen_twice)[0])))

        print("- Credentials Validation Passed!")

    def __validate_queries(self):
        print("+------------------------------------------------------------------+")
        print("| Validating Queries                                               |")
        print("+------------------------------------------------------------------+")
        queries_validated = True
        invalid_queries = []

        # Validating Environment Queries
        for q in self._query_execution.queries.values():
            query_parsed = q.replace('\n', '')
            query_parsed = re.sub(' +',' ', query_parsed).strip()
            query_type = self._query.get_query_type(q)
            if query_type == False:
                print('[NOT DETECTED] ' + query_parsed)
                queries_validated &= 0
                invalid_queries.append(query_parsed)
                self._progress.track_syntax(q)
            else:
                print('[{}] {}'.format(query_type.upper(), query_parsed))
                queries_validated &= 1

        # Validating Auxiliary Queries
        for q in self._query_execution.auxiliary_queries.values():
            query_type = self._query.get_query_type(q['query'])
            if query_type == False:
                print('[NOT DETECTED] {}'.format(q['query']))
                queries_validated &= 0
                invalid_queries.append(query_parsed)
            else:
                print('[{}] {}'.format(query_type.upper(), q['query']))
                queries_validated &= 1

        # Determine if the queries are validated
        if not queries_validated:
            self._progress.error("Queries not valid")
            raise Exception("- Validation Not Passed. Please review the above queries in the 'query_execution.py' file.")
        else:
            print("- Queries Validation Passed!")

    def __validate_regions(self):
        print("+------------------------------------------------------------------+")
        print("| Validating Regions                                               |")
        print("+------------------------------------------------------------------+")
        try:
            # Init validation
            progress = {}
            for region in self._credentials['environments'][self._args.environment]:
                progress[region['region']] = {}
            self._progress.track_validation(progress)

            # Start validation
            threads = []
            for region in self._credentials['environments'][self._args.environment]:
                validate_region = validate_regions(self._args, self._credentials, region)
                t = threading.Thread(target=validate_region.validate)
                t.progress = {}
                threads.append(t)
                t.start()

            # Wait all threads
            for t in threads:
                t.join()

            # Track Progress
            tracking = True
            error = False

            for t in threads:
                # Build progress dictionary
                progress[t.progress['region']] = { "success": t.progress['success'] }
                # Check SSH error
                if 'error' in t.progress:
                    error = True
                    progress[t.progress['region']]['error'] = t.progress['error']
                # Check SQL errors
                if 'errors' in t.progress:
                    error = True
                    progress[t.progress['region']]['errors'] = t.progress['errors']

            self._progress.track_validation(progress)

            # Check validation errors
            if error:
                error_msg = "- Regions Not Passed the Environment Validation."
                self._progress.error(error_msg[2:])
                raise Exception(error_msg)
            
            print("- Regions Validation Passed!")

        except KeyboardInterrupt:
            print("\n--> Ctrl+C received. Stopping the execution...")
            for t in threads:
                t.join()
            raise