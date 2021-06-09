import pymysql
import warnings
from collections import OrderedDict
from pymysql.cursors import DictCursorMixin, Cursor

class OrderedDictCursor(DictCursorMixin, Cursor):
    dict_type = OrderedDict

class mysql:
    def __init__(self):
        self._connection = None

    def connect(self, hostname, username, password, port, database):
        # Init Connection
        self._connection = pymysql.connect(host=hostname, user=username, password=password, port=port, db=database, charset='utf8mb4', use_unicode=True, cursorclass=pymysql.cursors.DictCursor, autocommit=False)

    def execute(self, query, args=None):
        try:
            try:
                # Check the connection
                self._connection.ping(reconnect=True)

                # Prepare the cursor
                with self._connection.cursor(OrderedDictCursor) as cursor:            
                    # Execute the SQL query ignoring warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        cursor.execute(query, args)

                    # Get the query results
                    query_result = cursor.fetchall() if not query.lstrip().startswith('INSERT INTO') else cursor.lastrowid

                # Commit the changes in the database
                self._connection.commit()

                # Return query results
                return query_result

            except (pymysql.err.OperationalError, pymysql.ProgrammingError, pymysql.InternalError, pymysql.IntegrityError, TypeError) as error:
                raise Exception(error.args[1])

        except Exception as e:
            try:
                print("--> Rollback Initiated...")
                self._connection.rollback()
                print("--> Rollback successfully performed.")
            except Exception as e2:
                print("--> Rollback not performed. Error: {}".format(e2))
            finally:
                if self._connection.open:
                    self._connection.close()
            raise e

        except KeyboardInterrupt:
            try:
                print("\n--> Rollback Initiated...")
                self._connection.rollback()
                print("--> Rollback successfully performed.")
            except Exception as e:
                print("--> Rollback not performed. Error: {}".format(e))
            finally:
                if self._connection.open:
                    self._connection.close()
            raise KeyboardInterrupt("Program Interrupted by User. Rollback successfully performed.")
