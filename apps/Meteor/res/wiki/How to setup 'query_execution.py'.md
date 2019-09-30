![](https://raw.githubusercontent.com/polius/Meteor/master/res/readme/meteor_header.png)

[**query_execution.py**](https://github.com/polius/Meteor/blob/master/app/query_execution.py) is a Python file that stores all the queries and logic that is going to use Meteor during the execution.

**This file is divided by:**

[**1.  Queries**](https://github.com/polius/Meteor/wiki/How-to-setup-'query_execution.py'#1-queries)

[**2.  Logic**](https://github.com/polius/Meteor/wiki/How-to-setup-'query_execution.py'#2-logic)

## 1. Queries

Meteor supports two type of queries:

*  **Basic** Queries
*  **Auxiliary** Queries

### Basic Queries

Basic Queries are the queries that are going to be executed during the execution process.

```
self._queries = {
    '1': "<query>",
    ...
}
```

Here's an example with 2 queries:

```
self._queries = {
    '1': "SELECT * FROM employees;",
    '2': "SELECT * FROM departments;"
}
```

### Auxiliary Queries

Auxiliary Queries are queries that are executed in other servers not included in the execution process.

```
self._auxiliary_queries = {
    '1': {"auxiliary_connection": "<auxiliary_connection_name>", "database": "<database>", "query": "<query>"},
    ...
}
```

These are the parameters needed:

*  **auxiliary_connection**: The auxiliary connection that is going to be used. This parameter is configured in the [**credentials.json**](https://github.com/polius/Meteor/wiki/How-to-setup-'credentials.json'#2-auxiliary-connections) file.
* **database**: The database where the query will be executed.
* **query**: The query that is going to execute.

To make it easy to understand imagine a deployment process that is executing the query "SELECT * FROM employees" in all databases in servers SQL1 and SQL2. Suppose that after all query executions a requirement was to execute another query "SELECT * FROM config" once in another Server (SQL4) and Database (settings).

In the above example, the setup should be:

```
# 'credentials.json' file
"auxiliary_connections":
{
    "sql4":
    {
        "hostname": "...",
        "username": "...",
        "password": "..."
    }
}

# 'query_execution.py' file
self._queries = {
    '1': "SELECT * FROM employees;"
}
self._auxiliary_queries = {
    '1': {"auxiliary_connection": "sql4", "database": "settings", "query": "SELECT * FROM config"}
}
```

## 2. Logic

Here is where the fun starts. Meteor has built-in three methods to easily manage the deployment.

*  **Before**
*  **Main**
*  **After**

### Before

This method wraps all the queries and logic that will be executed once per Region before all main executions.

```
def before(self, environment, region):
    # Insert here your code
```

### Main

This method wraps all the queries and logic that will be executed for every database in all region servers.

```
def main(self, environment, region, server, database):
    # Insert here your code
```

### After

This method wraps all the queries and logic that will be executed once per Region after being performed all main executions.

```
def after(self, environment, region):
    # Insert here your code
```

### How to execute queries

**Basic Queries**

```
self._meteor.execute(query=<query>, database=database)
```

**Example:** Execute the first query "SELECT * FROM employees;"

```
self._queries = {
    '1': "SELECT * FROM employees;",
    '2': "SELECT * FROM departments;"
}
```

```
self._meteor.execute(query=self._queries['1'], database=database)
```

Note that Basic Queries are only allowed in [main](https://github.com/polius/Meteor/wiki/How-to-setup-'query_execution.py'#main) method.

| **Method** | **Allowed** |
| ------ | ------ |
| before | 🔴 |
| main | ✅ |
| after | 🔴 |

**Auxiliary Queries**

```
self._meteor.execute(auxiliary=<auxiliary_connection_name>)
```

**Example**: Execute "SELECT * FROM config" in the database named "settings" using the Auxiliary Connection "sql4"

```
self._auxiliary_queries = {
    '1': {"auxiliary_connection": "sql4", "database": "settings", "query": "SELECT * FROM config"}
}
```

```
self._meteor.execute(auxiliary=self._auxiliary_queries['1'])
```

Auxiliary Queries are allowed in all methods.

| **Method** | **Allowed** |
| ------ | ------ |
| before | ✅ |
| main | ✅ |
| after | ✅ |