class query_template:
    def __init__(self):
        self._query_template = [
            {"startswith": "EXPLAIN ", "contains": "", "type": "Explain"},
            {"startswith": "SELECT ", "contains": "", "type": "Select"},
            {"startswith": "INSERT INTO ", "contains": "", "type": "Row_Level.Insert"},
            {"startswith": "INSERT IGNORE INTO ", "contains": "", "type": "Row_Level.Insert"},
            {"startswith": "REPLACE", "contains": "", "type": "Row_Level.Replace"},
            {"startswith": "UPDATE ", "contains": "", "type": "Row_Level.Update"},
            {"startswith": "DELETE ", "contains": "", "type": "Row_Level.Delete"},
            {"startswith": "CREATE ", "contains": " TABLE ", "type": "Table_Level.Create"},
            {"startswith": "DROP ", "contains": " TABLE ", "type": "Table_Level.Drop"},
            {"startswith": "TRUNCATE ", "contains": "", "type": "Table_Level.Truncate"},
            {"startswith": "ALTER TABLE ", "contains": " ADD FULLTEXT INDEX ", "type": "Table_Level.FullTextIndex.Add"},
            {"startswith": "ALTER TABLE ", "contains": " ADD INDEX ", "type": "Table_Level.Index.Add1"},
            {"startswith": "ALTER TABLE ", "contains": " ADD UNIQUE ", "type": "Table_Level.Index.Add1"},
            {"startswith": "ALTER TABLE", "contains": " DROP INDEX ", "type": "Table_Level.Index.Drop1"},
            {"startswith": "CREATE ", "contains": " INDEX ", "type": "Table_Level.Index.Add2"},
            {"startswith": "DROP INDEX ", "contains": "", "type": "Table_Level.Index.Drop2"},
            {"startswith": "ALTER TABLE ", "contains": " DROP PRIMARY KEY, ADD PRIMARY KEY", "type": "Table_Level.Primary_Key.Modify"},
            {"startswith": "ALTER TABLE ", "contains": " DROP PRIMARY KEY,ADD PRIMARY KEY", "type": "Table_Level.Primary_Key.Modify"},
            {"startswith": "ALTER TABLE ", "contains": " ADD PRIMARY KEY", "type": "Table_Level.Primary_Key.Add"},
            {"startswith": "ALTER TABLE ", "contains": " DROP PRIMARY KEY", "type": "Table_Level.Primary_Key.Drop"},
            {"startswith": "ALTER TABLE ", "contains": " ADD FOREIGN KEY ", "type": "Table_Level.Foreign_Key.Add"},
            {"startswith": "ALTER TABLE ", "contains": " DROP FOREIGN KEY ", "type": "Table_Level.Foreign_Key.Drop"},
            {"startswith": "ALTER TABLE ", "contains": " DROP PARTITION ", "type": "Table_Level.Alter.Partition.Drop"},
            {"startswith": "ALTER TABLE ", "contains": " REMOVE PARTITIONING", "type": "Table_Level.Alter.Partition.Remove_Partitioning"},
            {"startswith": "ALTER TABLE ", "contains": " ADD ", "type": "Table_Level.Alter.Add"},
            {"startswith": "ALTER TABLE ", "contains": " MODIFY ", "type": "Table_Level.Alter.Modify"},
            {"startswith": "ALTER TABLE ", "contains": " CHANGE ", "type": "Table_Level.Alter.Modify"},
            {"startswith": "ALTER TABLE ", "contains": " DROP ", "type": "Table_Level.Alter.Drop"},
            {"startswith": "ALTER TABLE ", "contains": " RENAME TO ", "type": "Table_Level.Alter.Rename"},
            {"startswith": "RENAME TABLE ", "contains": " TO ", "type": "Table_Level.Alter.Rename"},
            {"startswith": "ALTER TABLE ", "contains": " ROW_FORMAT = DYNAMIC", "type": "Database_Level.Alter.RowTable.Dynamic"},
            {"startswith": "ALTER TABLE ", "contains": " AUTO_INCREMENT", "type": "Table_Level.Alter.AutoIncrement"},
            {"startswith": "ALTER TABLE ", "contains": " CONVERT TO CHARACTER SET ", "type": "Table_Level.Alter.Convert"},
            {"startswith": "ALTER TABLE ", "contains": " COMMENT ", "type": "Table_Level.Alter.Comment"},
            {"startswith": "ALTER VIEW ", "contains": "", "type": "Table_Level.Alter.View"},
            {"startswith": "CREATE ", "contains": " TRIGGER ", "type": "Table_Level.Trigger.Add"},
            {"startswith": "DROP TRIGGER ", "contains": "", "type": "Table_Level.Trigger.Drop"},
            {"startswith": "OPTIMIZE TABLE ", "contains": "", "type": "Table_Level.Optimize_Table"},
            {"startswith": "CREATE DATABASE ", "contains": "", "type": "Database_Level.Database.Add"},
            {"startswith": "DROP DATABASE ", "contains": "", "type": "Database_Level.Database.Drop"},
            {"startswith": "CREATE ", "contains": " VIEW ", "type": "Database_Level.View.Add"},
            {"startswith": "DROP VIEW ", "contains": "", "type": "Database_Level.View.Drop"},
            {"startswith": "CREATE ", "contains": " FUNCTION ", "type": "Database_Level.Function.Create"},
            {"startswith": "DROP FUNCTION ", "contains": "", "type": "Database_Level.Function.Drop"},
            {"startswith": "CREATE ", "contains": " PROCEDURE ", "type": "Database_Level.Procedure.Create"},
            {"startswith": "DROP PROCEDURE ", "contains": "", "type": "Database_Level.Procedure.Drop"},
            {"startswith": "CALL ", "contains": "", "type": "Database_Level.Procedure.Call"},
            {"startswith": "", "contains": "CREATE EVENT ", "type": "Database_Level.Event.Create"},
            {"startswith": "", "contains": "CREATE IF NOT EXISTS EVENT ", "type": "Database_Level.Event.Create"},
            {"startswith": "DROP EVENT ", "contains": "", "type": "Database_Level.Event.Drop"},
            {"startswith": "SHOW ", "contains": "", "type": "Server_Level.Show"},
            {"startswith": "CREATE USER ", "contains": "", "type": "Server_Level.User.Create"},
            {"startswith": "DROP USER ", "contains": "", "type": "Server_Level.User.Drop"},
            {"startswith": "GRANT ", "contains": "", "type": "Server_Level.Privilege.Grant"},
            {"startswith": "REVOKE ", "contains": "", "type": "Server_Level.Privilege.Revoke"},
            {"startswith": "SET GLOBAL ", "contains": "", "type": "Server_Level.Set_Global"},
            {"startswith": "SET ", "contains": "", "type": "Server_Level.Set_Local"}
        ]

    @property
    def query_template(self):
        return self._query_template

    def validate_execution(self, query_raw, args, connection, database_name=None):
        query_string = query_raw.replace('`','') % args if args else query_raw.replace('`','')
        query_lower = query_string.lower()

        for t in self._query_template:
            if query_lower.startswith(t["startswith"].lower()) and t["contains"].lower() in query_lower:
                if t["type"] == 'Select':
                    # connection.execute('EXPLAIN ' + query_raw, database_name)
                    break
                elif t["type"].startswith("Row_Level"):
                    if t["type"] == "Row_Level.Insert":
                        connection.execute('EXPLAIN ' + query_raw, args, database_name)
                    elif t["type"] == "Row_Level.Replace":
                        connection.execute('EXPLAIN ' + query_raw, args, database_name)
                    elif t["type"] == "Row_Level.Update":
                        connection.execute('EXPLAIN ' + query_raw, args, database_name)
                    elif t["type"] == "Row_Level.Delete":
                        connection.execute('EXPLAIN ' + query_raw, args, database_name)
                    break

                elif t["type"].startswith("Table_Level"):
                    if t["type"] == "Table_Level.Create":
                        # Check Table
                        table_name = query_string.split(" ")[5] if 'if not exists' in query_lower else query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if exists:
                            raise Exception("Table '{}.{}' already exists'".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Drop":
                        # Check Table
                        table_name = query_string.split(" ")[4] if 'if exists' in query_lower else query_string.split(" ")[2]
                        table_name = table_name[:-1] if table_name.endswith(';') else table_name
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Truncate":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        table_name = table_name[:-1] if table_name.endswith(';') else table_name
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.FullTextIndex.Add":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        for p in query_string[query_string.index('(') + 1:-2].split(','):
                            column_name = p.strip().split("(")[0].replace('`', '')
                            if column_name.find('(') != -1:
                                column_name = column_name[:column_name.find('(')]
                            exists = connection.check_column_exists(database_name, table_name, column_name)
                            if not exists:
                                raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column_name, database_name, table_name))

                        # Check Index
                        index_name = query_string.split(" ")[6]
                        if '(' in index_name:
                            index_name = index_name[:index_name.index('(')]
                        exists = connection.check_index_exists(database_name, table_name, index_name)
                        if exists:
                            raise Exception("Index '{}' already exists in '{}.{}'".format(index_name, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Index.Add1":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Columns
                        for p in query_string[query_string.index('(') + 1:-2].split(','):
                            column_name = p.strip().replace('`', '')
                            if column_name.find('(') != -1:
                                column_name = column_name[:column_name.find('(')]
                            exists = connection.check_column_exists(database_name, table_name, column_name)
                            if not exists:
                                column_parsed = p.strip().replace('`', '').replace('`', '')
                                raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column_parsed, database_name, table_name))

                        # Check Index
                        index_name = query_string.split(" ")[6] if ' UNIQUE INDEX ' in query_string else query_string.split(" ")[5]
                        if '(' in index_name:
                            index_name = index_name[:index_name.index('(')]
                        exists = connection.check_index_exists(database_name, table_name, index_name)
                        if exists:
                            raise Exception("Index '{}' already exists in '{}.{}'".format(index_name, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Index.Drop1":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '" + table_name + "' does not exist in '" + database_name + "'.")

                        # Check Index
                        index_name = query_string.split(" ")[-1]
                        index_name = index_name[:-1] if index_name.endswith(';') else index_name
                        exists = connection.check_index_exists(database_name, table_name, index_name)
                        if not exists:
                            raise Exception("Index '{}' doesn't exist in '{}.{}'".format(index_name, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Index.Add2":
                        # Check Table
                        unique = 1 if ' UNIQUE ' in query_string else 0
                        table_name = query_string.split(" ")[4 + unique]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Columns
                        for p in query_string[query_string.index('(') + 1:-2].split(','):
                            exists = connection.check_column_exists(database_name, table_name, p.strip().replace('`', '').replace('`', ''))
                            if not exists:
                                raise Exception("Column '" + p.strip().replace('`', '').replace('`', '') + "' does not exist in '" + database_name + "." + table_name + "'.")
                        # Check Index
                        index_name = query_string.split(" ")[2 + unique]
                        exists = connection.check_index_exists(database_name, table_name, index_name)
                        if exists:
                            raise Exception("Index '{}' already exists in '{}.{}'".format(index_name, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Index.Drop2":
                        # Check Table
                        table_name = query_string.split(" ")[4]
                        table_name = table_name[:-1] if table_name.endswith(';') else table_name
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Index
                        index_name = query_string.split(" ")[2]
                        exists = connection.check_index_exists(database_name, table_name, index_name)
                        if not exists:
                            raise Exception("Index '{}' doesn't exist in '{}.{}'".format(index_name, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Primary_Key.Add":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Columns
                        for p in query_string[query_string.index('(') + 1:-2].split(','):
                            exists = connection.check_column_exists(database_name, table_name, p.strip().replace('`', '').replace('`', ''))
                            if not exists:
                                column_parsed = p.strip().replace('`', '').replace('`', '')
                                raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column_parsed, database_name, table_name))

                        # Check PK
                        exists = connection.check_pk_exists(database_name, table_name)
                        if exists:
                            raise Exception("Table '{}.{}' already has a Primary Key".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Primary_Key.Drop":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check PK
                        exists = connection.check_pk_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't have a Primary Key".format(database_name, table_name))
                        break
                    
                    elif t["type"] == "Table_Level.Primary_Key.Modify":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check PK
                        exists = connection.check_pk_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't have a Primary Key".format(database_name, table_name))

                        # Check if the same PK Exists
                        start = query_string.find('(')
                        end = query_string.find(')')
                        pks = query_string[start+1:end].replace('`','').split(',')

                        # Check PK
                        exists = connection.check_pk_exists_columns(database_name, table_name, pks)
                        if exists:
                            raise Exception("Table '{}.{}' has the same Primary Key".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Foreign_Key.Add":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        column_name = query_string.split(" ")[6].strip().replace('(', '').replace(')', '').replace('`', '')
                        exists = connection.check_column_exists(database_name, table_name, column_name)
                        if not exists:
                            raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column_name, database_name, table_name))

                        # Check FK
                        exists = connection.check_fk_exists(database_name, table_name, column_name)
                        if exists:
                            raise Exception("Table '{}.{}' already has a Foreign Key".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Foreign_Key.Drop":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        foreign_name = query_string.split(" ")[6]
                        foreign_name = foreign_name[:-1] if foreign_name.endswith(';') else foreign_name
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check FK
                        exists = connection.check_fk_exists_by_name(database_name, table_name, foreign_name)
                        if not exists:
                            raise Exception("Foreign Key '{}' doesn't exist in '{}.{}'".format(foreign_name, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.Partition.Drop":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Partition
                        partition_name = query_string.split(" ")[5]
                        partition_name = partition_name[:-1] if partition_name.endswith(';') else partition_name
                        exists = connection.check_partition_exists(database_name, table_name, partition_name)
                        if not exists:
                            raise Exception("Partition '{}' doesn't exist in '{}.{}'".format(partition_name, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.Partition.Remove_Partitioning":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.Add":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        column = 1 if " COLUMN " in query_string else 0
                        column = query_string.split(" ")[4 + column].replace('`', '')
                        exists = connection.check_column_exists(database_name, table_name, column)
                        if exists:
                            raise Exception("Column '{}' already exists in '{}.{}'".format(column, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.Modify":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        column = 1 if " COLUMN " in query_string else 0
                        column = query_string.split(" ")[4 + column].replace('`', '')
                        exists = connection.check_column_exists(database_name, table_name, column)
                        if not exists:
                            raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.Drop":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Column
                        column = 1 if " COLUMN " in query_string else 0
                        column = query_string.split(" ")[4 + column].replace('`', '')
                        column = column[:-1] if column.endswith(';') else column
                        exists = connection.check_column_exists(database_name, table_name, column)
                        if not exists:
                            raise Exception("Column '{}' doesn't exist in '{}.{}'".format(column, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.Rename":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))
                        break

                    elif t["type"] == "Database_Level.Alter.RowTable.Dynamic":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check RowFormat
                        row_format = connection.check_row_format(database_name, table_name)
                        if row_format == 'Dynamic':
                            raise Exception("Table '{}.{}' already has ROW_FORMAT=DYNAMIC".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.AutoIncrement":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.Convert":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Alter.View":
                        # Check View
                        view_name = query_string.split(" ")[2]
                        exists = connection.check_view_exists(database_name, view_name)
                        if not exists:
                            raise Exception("View '{}.{}' doesn't exist".format(database_name, view_name))
                        break

                    elif t["type"] == "Table_Level.Trigger.Add":
                        # Check Table
                        table_name = query_string[query_lower.index('on'):].split(" ")[1].strip()
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))

                        # Check Trigger
                        trigger_name = query_string[query_lower.index('trigger'):].split(" ")[1].strip()
                        exists = connection.check_trigger_exists(database_name, table_name, trigger_name)
                        if exists:
                            raise Exception("Trigger '{}' already exists in '{}.{}'".format(trigger_name, database_name, table_name))
                        break

                    elif t["type"] == "Table_Level.Trigger.Drop":
                        # Check Trigger
                        if 'if exists' in query_lower:
                            trigger_name = query_string[query_lower.index('trigger'):-1].split(" ")[3].strip()
                        else:
                            trigger_name = query_string[query_lower.index('trigger'):-1].split(" ")[1].strip()
                        exists = connection.check_trigger_exists(database_name, '%', trigger_name)
                        if not exists:
                            raise Exception("Trigger '{}' doesn't exist in '{}'".format(trigger_name, database_name))
                        break

                    elif t["type"] == "Table_Level.Optimize_Table":
                        # Check Table
                        table_name = query_string.split(" ")[2]
                        table_name = table_name[:-1] if table_name.endswith(';') else table_name
                        exists = connection.check_table_exists(database_name, table_name)
                        if not exists:
                            raise Exception("Table '{}.{}' doesn't exist".format(database_name, table_name))
                        break

                elif t["type"].startswith("Database_Level"):
                    if t["type"] == "Database_Level.Database.Add":
                        # Check DB
                        database_name = query_string.split(" ")[2]
                        database_name = database_name[:-1] if database_name.endswith(';') else database_name
                        exists = connection.check_db_exists(database_name)
                        if exists:
                            raise Exception("Database '{}' already exists".format(database_name))
                        break

                    elif t["type"] == "Database_Level.Database.Drop":
                        # Check DB
                        database_name = query_string.split(" ")[4] if 'if exists' in query_lower else query_string.split(" ")[2]
                        database_name = database_name[:-1] if database_name.endswith(';') else database_name
                        exists = connection.check_db_exists(database_name)
                        if not exists:
                            raise Exception("Database '{}' doesn't exist".format(database_name))
                        break

                    elif t["type"] == "Database_Level.View.Add":
                        # Check View
                        view_name = query_string[query_lower.index('view'):].split(" ")[1].strip()
                        exists = connection.check_view_exists(database_name, view_name)
                        if exists:
                            raise Exception("View '{}.{}' already exists".format(database_name, view_name))
                        break

                    elif t["type"] == "Database_Level.View.Drop":
                        # Check View
                        view_name = query_string[query_lower.index('view'):].split(" ")[3].strip() if 'if exists' in query_lower else query_string[query_lower.index('view'):].split(" ")[1].strip()
                        view_name = view_name[:-1] if view_name.endswith(';') else view_name
                        exists = connection.check_view_exists(database_name, view_name)
                        if not exists:
                            raise Exception("View '{}.{}' doesn't exist".format(database_name, view_name))
                        break

                    elif t["type"] == "Database_Level.Function.Create":
                        # Check Function
                        function_name = query_string[query_lower.index('function'):].split(" ")[1].strip()
                        exists = connection.check_function_exists(database_name, function_name)
                        if exists:
                            raise Exception("Function '{}' already exists in '{}'".format(function_name, database_name))
                        break

                    elif t["type"] == "Database_Level.Function.Drop":
                        # Check Function
                        function_name = query_string.split(" ")[2]
                        function_name = function_name[:-1] if function_name.endswith(';') else function_name
                        exists = connection.check_function_exists(database_name, function_name)
                        if not exists:
                            raise Exception("Function '{}' doesn't exist in '{}'".format(function_name, database_name))
                        break

                    elif t["type"] == "Database_Level.Procedure.Create":
                        # Check Procedure
                        procedure_name = query_string[query_lower.index('procedure'):].split(" ")[1].strip()
                        exists = connection.check_procedure_exists(database_name, procedure_name)
                        if exists:
                            raise Exception("Procedure '{}' already exists in '{}'".format(procedure_name, database_name))
                        break

                    elif t["type"] == "Database_Level.Procedure.Drop":
                        # Check Procedure
                        procedure_name = query_string[query_lower.index('procedure'):].split(" ")[1].strip()
                        procedure_name = procedure_name[:-1] if procedure_name.endswith(';') else procedure_name
                        exists = connection.check_procedure_exists(database_name, procedure_name)
                        if not exists:
                            raise Exception("Procedure '{}' doesn't exist in '{}'".format(procedure_name, database_name))
                        break

                    elif t["type"] == "Database_Level.Procedure.Call":
                        # Check Procedure
                        procedure_name = query_string.split(" ")[1].strip()[:query_string.split(" ")[1].strip().index('(')]
                        exists = connection.check_procedure_exists(database_name, procedure_name)
                        if not exists:
                            raise Exception("Procedure '{}' doesn't exist in '{}'".format(procedure_name, database_name))
                        break

                    elif t["type"] == "Database_Level.Event.Create":
                        # Check Event
                        if 'if not exists' in query_lower:
                            event_name = query_string[query_lower.index('event'):].split(" ")[4].strip()
                        else:
                            event_name = query_string[query_lower.index('event'):].split(" ")[1].strip()
                        exists = connection.check_event_exists(event_name)
                        if exists:
                            raise Exception("Event '{}' already exists in '{}'".format(event_name, database_name))
                        break

                    elif t["type"] == "Database_Level.Event.Drop":
                        # Check Event
                        event_name = query_string[query_lower.index('event'):].split(" ")[1].strip()
                        event_name = event_name[:-1] if event_name.endswith(';') else event_name
                        exists = connection.check_event_exists(event_name)
                        if not exists:
                            raise Exception("Event '{}' doesn't exist in '{}'".format(event_name, database_name))
                        break

                elif t["type"].startswith("Server_Level"):
                    if t["type"] == "Server_Level.Show":
                        break

                    elif t["type"] == "Server_Level.User.Create":
                        # Check if the user already exists
                        username = query_string.replace("'", '"').split('"')[1]
                        hostname = query_string.replace("'", '"').split('"')[3]
                        exists = connection.check_user_exists(username, hostname)
                        if exists:
                            raise Exception("User '{}'@'{}' already exists".format(username, hostname))
                        break

                    elif t["type"] == "Server_Level.User.Drop":
                        # Check if the user already exists
                        username = query_string.replace("'", '"').split('"')[1]
                        hostname = query_string.replace("'", '"').split('"')[3]
                        exists = connection.check_user_exists(username, hostname)
                        if not exists:
                            raise Exception("User '{}'@'{}' doesn't exist".format(username, hostname))
                        break

                    elif t["type"] == "Server_Level.Set_Global":
                        break

                    elif t["type"] == "Server_Level.Set_Local":
                        break
        return True
