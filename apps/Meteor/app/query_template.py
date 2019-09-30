#!/usr/bin/env python
# -*- coding: utf-8 -*-

class query_template:
    def __init__(self, query_template):
        self._query_template = query_template

    def validate_execution(self, query_raw, connection, database_name=None):
        query_string = query_raw.replace('`','')
        query_lower = query_string.lower()

        for t in self._query_template:
            if query_lower.startswith(t["startswith"].lower()) and t["contains"].lower() in query_lower:
                if t["type"] == 'Select':
                    # connection.execute('EXPLAIN ' + query_raw, database_name)
                    break

                elif t["type"].startswith("Row_Level"):
                    if t["type"] == "Row_Level.Insert":
                        connection.execute('EXPLAIN ' + query_raw, database_name)

                    elif t["type"] == "Row_Level.Replace":
                        connection.execute('EXPLAIN ' + query_raw, database_name)

                    elif t["type"] == "Row_Level.Update":
                        connection.execute('EXPLAIN ' + query_raw, database_name)

                    elif t["type"] == "Row_Level.Delete":
                        connection.execute('EXPLAIN ' + query_raw, database_name)

                    break

                elif t["type"].startswith("Table_Level"):
                    if t["type"] == "Table_Level.Create":
                        # Check Table
                        if 'if not exists' in query_lower:
                            table_name = query_string.split(" ")[5]
                        else:
                            table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is True:
                            raise Exception("Table '{}.{}' already exists'".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Drop":

                        if 'if exists' in query_lower:
                            table_name = query_string.split(" ")[4]
                        else:
                            table_name = query_string.split(" ")[2]

                        table_name = table_name[:-1] if table_name.endswith(';') else table_name

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Truncate":

                        table_name = query_string.split(" ")[2]

                        if table_name[-1] == ';':
                            table_name = table_name[:-1]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.FullTextIndex.Add":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        for p in query_string[query_string.index('(') + 1:-2].split(','):
                            column_name = p.strip().split("(")[0].replace('`', '')

                            if column_name.find('(') != -1:
                                column_name = column_name[:column_name.find('(')]

                            exists = connection.check_column_exists(database_name, table_name, column_name)

                            if exists is False:
                                raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column_name, database_name, table_name))

                        # Check Index
                        index_name = query_string.split(" ")[6]

                        if '(' in index_name:
                            index_name = index_name[:index_name.index('(')]

                        exists = connection.check_index_exists(database_name, table_name, index_name)

                        if exists is True:
                            raise Exception("Index '{}' already exists in '{}.{}'".format(index_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Index.Add1":

                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Columns
                        for p in query_string[query_string.index('(') + 1:-2].split(','):
                            column_name = p.strip().replace('`', '')

                            if column_name.find('(') != -1:
                                column_name = column_name[:column_name.find('(')]

                            exists = connection.check_column_exists(database_name, table_name, column_name)

                            if exists is False:
                                column_parsed = p.strip().replace('`', '').replace('`', '')
                                raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column_parsed, database_name, table_name))

                        # Check Index
                        index_name = ""

                        if " UNIQUE INDEX " in query_string:
                            index_name = query_string.split(" ")[6]
                        else:
                            index_name = query_string.split(" ")[5]

                        if '(' in index_name:
                            index_name = index_name[:index_name.index('(')]

                        exists = connection.check_index_exists(database_name, table_name, index_name)

                        if exists is True:
                            raise Exception("Index '{}' already exists in '{}.{}'".format(index_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Index.Drop1":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '" + table_name + "' does not exist in '" + database_name + "'.")

                        # Check Index
                        index_name = query_string.split(" ")[-1][:-1]
                        exists = connection.check_index_exists(database_name, table_name, index_name)

                        if exists is False:
                            raise Exception("Index '{}' doesn't exist in '{}.{}'".format(index_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Index.Add2":
                        unique = 0

                        if ' UNIQUE ' in query_string:
                            unique = 1

                        table_name = query_string.split(" ")[4 + unique]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Columns
                        for p in query_string[query_string.index('(') + 1:-2].split(','):
                            exists = connection.check_column_exists(database_name, table_name, p.strip().replace('`', '').replace('`', ''))

                            if exists is False:
                                raise Exception("Column '" + p.strip().replace('`', '').replace('`', '') + "' does not exist in '" + database_name + "." + table_name + "'.")

                        # Check Index
                        index_name = query_string.split(" ")[2 + unique]
                        exists = connection.check_index_exists(database_name, table_name, index_name)

                        if exists is True:
                            raise Exception("Index '{}' already exists in '{}.{}'".format(index_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Index.Drop2":
                        table_name = query_string.split(" ")[4][:-1]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Index
                        index_name = query_string.split(" ")[2]
                        exists = connection.check_index_exists(database_name, table_name, index_name)

                        if exists is False:
                            raise Exception("Index '{}' doesn't exist in '{}.{}'".format(index_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Primary_Key.Add":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Columns
                        for p in query_string[query_string.index('(') + 1:-2].split(','):
                            exists = connection.check_column_exists(database_name, table_name, p.strip().replace('`', '').replace('`', ''))

                            if exists is False:
                                column_parsed = p.strip().replace('`', '').replace('`', '')
                                raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column_parsed, database_name, table_name))

                        # Check PK
                        exists = connection.check_pk_exists(database_name, table_name)

                        if exists is True:
                            raise Exception("Table '{}.{}' already has a Primary Key".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Primary_Key.Drop":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check PK
                        exists = connection.check_pk_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't have a Primary Key".format(database_name, table_name))

                        break
                    
                    elif t["type"] == "Table_Level.Primary_Key.Modify":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check PK
                        exists = connection.check_pk_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't have a Primary Key".format(database_name, table_name))

                        # Check if the same PK Exists
                        start = query_string.find('(')
                        end = query_string.find(')')
                        pks = query_string[start+1:end].replace('`','').split(',')

                        # Check PK
                        exists = connection.check_pk_exists_columns(database_name, table_name, pks)

                        if exists is True:
                            raise Exception("Table '{}.{}' has the same Primary Key".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Foreign_Key.Add":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        column_name = query_string.split(" ")[6].strip().replace('(', '').replace(')', '').replace('`', '')

                        exists = connection.check_column_exists(database_name, table_name, column_name)

                        if exists is False:
                            raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column_parsed, database_name, table_name))

                        # Check FK
                        exists = connection.check_fk_exists(database_name, table_name, column_name)

                        if exists is True:
                            raise Exception("Table '{}.{}' already has a Foreign Key".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Foreign_Key.Drop":
                        table_name = query_string.split(" ")[2]
                        foreign_name = query_string.split(" ")[6][:-1]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check FK
                        exists = connection.check_fk_exists_by_name(database_name, table_name, foreign_name)

                        if exists is False:
                            raise Exception("Foreign Key '{}' doesn't exist in '{}.{}'".format(foreign_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.Partition.Drop":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Partition
                        partition_name = query_string.split(" ")[5]
                        partition_name = partition_name[:-1] if partition_name.endswith(';') else partition_name
                        exists = connection.check_partition_exists(database_name, table_name, partition_name)

                        if exists is False:
                            raise Exception("Partition '{}' doesn't exist in '{}.{}'".format(partition_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.Partition.Remove_Partitioning":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.Add":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        column = 0

                        if " COLUMN " in query_string:
                            column = 1

                        column = query_string.split(" ")[4 + column].replace('`', '')
                        exists = connection.check_column_exists(database_name, table_name, column)

                        if exists is True:
                            raise Exception("Column '{}' already exists in '{}.{}'".format(column, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.Modify":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        column = 0

                        if " COLUMN " in query_string:
                            column = 1

                        column = query_string.split(" ")[4 + column].replace('`', '')
                        exists = connection.check_column_exists(database_name, table_name, column)

                        if exists is False:
                            raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.Drop":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        column = 0

                        if " COLUMN " in query_string:
                            column = 1

                        column = query_string.split(" ")[4 + column][:-1].replace('`', '')
                        exists = connection.check_column_exists(database_name, table_name, column)

                        if exists is False:
                            raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.Rename":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        break

                    elif t["type"] == "Database_Level.Alter.RowTable.Dynamic":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check RowFormat
                        row_format = connection.check_row_format(database_name, table_name)

                        if row_format == 'Dynamic':
                            raise Exception("Table '{}.{}' already has ROW_FORMAT=DYNAMIC".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.AutoIncrement":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.Convert":
                        table_name = query_string.split(" ")[2]

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Alter.View":
                        # Check View
                        view_name = query_string.split(" ")[2]
                        exists = connection.check_view_exists(database_name, view_name)

                        if exists is False:
                            raise Exception("View '{}.{}' doesn't exist".format(database_name, view_name))

                        break

                    elif t["type"] == "Table_Level.Trigger.Add":
                        table_name = query_string[query_lower.index('on'):].split(" ")[1].strip()

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Trigger
                        trigger_name = query_string[query_lower.index('trigger'):].split(" ")[1].strip()
                        exists = connection.check_trigger_exists(database_name, table_name, trigger_name)

                        if exists is True:
                            raise Exception("Trigger '{}' already exists in '{}.{}'".format(trigger_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Trigger.Drop":
                        # Check Trigger
                        trigger_name = ""

                        if 'if exists' in query_lower:
                            trigger_name = query_string[query_lower.index('trigger'):-1].split(" ")[3].strip()
                        else:
                            trigger_name = query_string[query_lower.index('trigger'):-1].split(" ")[1].strip()

                        exists = connection.check_trigger_exists(database_name, '%', trigger_name)

                        if exists is False:
                            raise Exception("Trigger '{}' doesn't exist in '{}.{}'".format(trigger_name, database_name, table_name))

                        break

                    elif t["type"] == "Table_Level.Optimize_Table":
                        table_name = query_string.split(" ")[2]
                        table_name = table_name[:-1] if table_name.endswith(';') else table_name

                        # Check Table
                        exists = connection.check_table_exists(database_name, table_name)

                        if exists is False:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        break

                elif t["type"].startswith("Database_Level"):

                    if t["type"] == "Database_Level.Database.Add":
                        # Check DB
                        database_name = query_string.split(" ")[2]
                        exists = connection.check_db_exists(database_name)

                        if exists is True:
                            raise Exception("Database '{}' already exists".format(database_name))

                        break

                    elif t["type"] == "Database_Level.Database.Drop":
                        # Check DB
                        if 'if exists' in query_lower:
                            database_name = query_string.split(" ")[4][:-1]
                        else:
                            database_name = query_string.split(" ")[2][:-1]

                        exists = connection.check_db_exists(database_name)

                        if exists is False:
                            raise Exception("Database '{}' doesn't exist".format(database_name))

                        break

                    elif t["type"] == "Database_Level.View.Add":
                        # Check View
                        view_name = query_string[query_lower.index('view'):].split(" ")[1].strip()[:-1]
                        exists = connection.check_view_exists(database_name, view_name)

                        if exists is True:
                            raise Exception("View '{}.{}' already exists".format(database_name, view_name))

                        break

                    elif t["type"] == "Database_Level.View.Drop":
                        # Check View
                        if 'if exists' in query_lower:
                            view_name = query_string[query_lower.index('view'):].split(" ")[3].strip()[:-1]
                        else:
                            view_name = query_string[query_lower.index('view'):].split(" ")[1].strip()[:-1]

                        exists = connection.check_view_exists(database_name, view_name)

                        if exists is False:
                            raise Exception("View '{}.{}' doesn't exist".format(database_name, view_name))

                        break

                    elif t["type"] == "Database_Level.Function.Create":
                        # Check Function
                        function_name = query_string[query_lower.index('function'):].split(" ")[1].strip()
                        exists = connection.check_function_exists(database_name, function_name)

                        if exists is True:
                            raise Exception("Function '{}' already exists in '{}'".format(function_name, database_name))

                        break

                    elif t["type"] == "Database_Level.Function.Drop":
                        # Check Function
                        function_name = query_string.split(" ")[2][:-1]
                        exists = connection.check_function_exists(database_name, function_name)

                        if exists is False:
                            raise Exception("Function '{}' doesn't exist in '{}'".format(function_name, database_name))

                        break

                    elif t["type"] == "Database_Level.Procedure.Create":
                        # Check Procedure
                        procedure_name = query_string[query_lower.index('procedure'):].split(" ")[1].strip()
                        exists = connection.check_procedure_exists(database_name, procedure_name)

                        if exists is True:
                            raise Exception("Procedure '{}' already exists in '{}'".format(procedure_name, database_name))

                        break

                    elif t["type"] == "Database_Level.Procedure.Drop":
                        # Check Procedure
                        procedure_name = query_string[query_lower.index('procedure'):].split(" ")[1].strip()[:-1]
                        exists = connection.check_procedure_exists(database_name, procedure_name)

                        if exists is False:
                            raise Exception("Procedure '{}' doesn't exist in '{}'".format(procedure_name, database_name))

                        break

                    elif t["type"] == "Database_Level.Procedure.Call":
                        # Check Procedure
                        procedure_name = query_string.split(" ")[1].strip()[:query_string.split(" ")[1].strip().index('(')]
                        exists = connection.check_procedure_exists(database_name, procedure_name)

                        if exists is False:
                            raise Exception("Procedure '{}' doesn't exist in '{}'".format(procedure_name, database_name))

                        break

                    elif t["type"] == "Database_Level.Event.Create":
                        # Check Event
                        if 'if not exists' in query_lower:
                            event_name = query_string[query_lower.index('event'):].split(" ")[4].strip()
                        else:
                            event_name = query_string[query_lower.index('event'):].split(" ")[1].strip()

                        exists = connection.check_event_exists(event_name)

                        if exists is True:
                            raise Exception("Event '{}' already exists in '{}'".format(event_name, database_name))

                        break

                    elif t["type"] == "Database_Level.Event.Drop":
                        # Check Event
                        event_name = query_string[query_lower.index('event'):].split(" ")[1].strip()[:-1]
                        exists = connection.check_event_exists(event_name)

                        if exists is False:
                            raise Exception("Event '{}' doesn't exist in '{}'".format(event_name, database_name))

                        break

                elif t["type"].startswith("Server_Level"):
                    if t["type"] == "Server_Level.Show":
                        break

                    elif t["type"] == "Server_Level.User.Create":
                        username = query_string.replace("'", '"').split('"')[1]
                        hostname = query_string.replace("'", '"').split('"')[3]

                        # Check if the user already exists
                        exists = connection.check_user_exists(username, hostname)

                        if exists is True:
                            raise Exception("User '{}'@'{}' already exists".format(username, hostname))

                        break

                    elif t["type"] == "Server_Level.User.Drop":
                        username = query_string.replace("'", '"').split('"')[1]
                        hostname = query_string.replace("'", '"').split('"')[3]

                        # Check if the user already exists
                        exists = connection.check_user_exists(username, hostname)

                        if exists is False:
                            raise Exception("User '{}'@'{}' doesn't exist".format(username, hostname))

                        break

                    elif t["type"] == "Server_Level.Set_Global":
                        break

                    elif t["type"] == "Server_Level.Set_Local":
                        break

        return True
