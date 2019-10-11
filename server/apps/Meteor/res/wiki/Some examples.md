![](https://raw.githubusercontent.com/polius/Meteor/master/res/readme/meteor_header.png)

The aim of this section is to fully understand how to execute some queries by giving some practical examples:

**Basic Queries**

*  [**Example 1**](https://github.com/polius/Meteor/wiki/Some-examples#basic-queries---example-1)
*  [**Example 2**](https://github.com/polius/Meteor/wiki/Some-examples#basic-queries---example-2)

**Auxiliary Queries**

*  [**Example 1**](https://github.com/polius/Meteor/wiki/Some-examples#auxiliary-queries---example-1)
*  [**Example 2**](https://github.com/polius/Meteor/wiki/Some-examples#auxiliary-queries---example-2)

## Basic Queries - Example 1

**USE CASE**

Execute a "SELECT * FROM employees" in all databases.

**APPLICATION**

```
self._queries = {
    '1': "SELECT * FROM employees;"
}
```

```
def before(self, environment, region):
    pass
  
def main(self, environment, region, server, database):
    self._meteor.execute(query=self._queries['1'], database=database)

def after(self, environment, region):
    pass
```

## Basic Queries - Example 2

**USE CASE**

Execute a "SELECT * FROM employees" in all database that ends with '_vip'.

**APPLICATION**

```
self._queries = {
    '1': "SELECT * FROM employees;"
}
```

```
def before(self, environment, region):
    pass
  
def main(self, environment, region, server, database):
    if database.endswith('_vip'):
        self._meteor.execute(query=self._queries['1'], database=database)

def after(self, environment, region):
    pass
```

## Auxiliary Queries - Example 1

**USE CASE**

Get the employees that earns the highest salary (in the DBs that ends with '_vip', table 'employees') and insert their IDs and salary to another DB named 'vips', table 'bosses' located in the server 'sql4' (server not included in the execution process).

**APPLICATION**

```
self._queries = {
    '1': """
           SELECT id, salary
           FROM employees
           WHERE salary = (SELECT MAX(salary) FROM employees);
         """
}

self._auxiliary_queries = {
    '1': {"auxiliary_connection": "sql4", "database": "vips", "query": ""}
}
```

- Note that before executing this auxiliary query an auxiliary connection should be configured in the 'credentials.json' file.

```
def before(self, environment, region):
    pass
  
def main(self, environment, region, server, database):
    if database.endswith('_vip'):
        # Get the highest paid employees
        employees = self._meteor.execute(query=self._queries['1'], database=database)
        # Check if the query returns rows (so the table is not empty)
        if len(employees) > 0:
            # For every employee returned, insert their id and salary into the server 'sql4', database 'vips', table 'bosses'
            for employee in employees:
                # Prepare the auxiliary query
                self._auxiliary_queries['1']['query'] = "INSERT INTO bosses (id, salary) VALUES ({},{});".format(employee['id'], employee['salary'])
                # Execute the auxiliary query
                self._meteor.execute(auxiliary=self._auxiliary_queries['1'])

def after(self, environment, region):
    pass
```

## Auxiliary Queries - Example 2

**USE CASE**

In the server 'sql4' (server not included in the execution process), database 'vips', table 'bosses' stores some information related about the most relevant employees in the company.

The aim is to know if exists employees that earn more than the highest paid boss. These employees are stored in servers sql1, sql2 and sql3 (servers included in the execution process), databases that ends with '_emp', table 'employees'.

**APPLICATION**

```
self._queries = {
    '1': "SELECT id, name FROM employees WHERE salary > {};",
}

self._auxiliary_queries = {
    '1': {"auxiliary_connection": "sql4", "database": "vips", "query": "SELECT MAX(salary) AS 'salary' FROM bosses;"}
}
```

- Note that before executing this auxiliary query, an auxiliary connection should be configured in the 'credentials.json' file.

```
def before(self, environment, region):
    # Get the highest paid boss
    self._salary = self._meteor.execute(auxiliary=self._auxiliary_queries['1'])
  
def main(self, environment, region, server, database):
    if database.endswith('_emp'):
        # Check if the auxiliary query returns a row (so the table is not empty)
        if len(self._salary) > 0:
            # Get employees that earn a higher salary than the highest paid boss
            self._meteor.execute(query=self._queries['1'].format(self._salary[0]['salary']), database=database)

def after(self, environment, region):
    pass
```