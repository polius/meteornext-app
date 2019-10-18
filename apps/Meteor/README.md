[![Python version](https://img.shields.io/badge/python-2.7%20|%203.6%20|%203.7-blue.svg)](https://www.python.org/downloads/)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

![](res/readme/meteor_header.png?raw=true)

**A complete Python application to automatize the SQL Mass Deployment process making it easy and simple**

Meteor uses cutting-edge technologies like Parallel Executions which notably reduces the deployment duration in a logarithmic scale. Also allows to perform Cross-Region Executions avoiding transport delay.

Meteor is built leading to an end-to-end validation process to guarantee that no queries will harm any environment.

Tested in a real Production Environment using:

- MySQL (5.6 / 5.7)
- Amazon RDS for MySQL (5.6 / 5.7)
- Amazon Aurora MySQL (5.6 / 5.7)
- Amazon Aurora Serverless

[Checkout the demo](https://meteor.poliuscorp.com)

# 1. INSTALLATION

### 1.1. Clone the Meteor Repository

```
$ git clone https://github.com/polius/Meteor.git
```

### 1.2. Install the Requirements

```
$ cd Meteor/app/
$ pip install -r requirements.txt --user
```

# 2. SETUP

Before executing the Meteor, there are two files that have to be filled:

### credentials.json

[How to setup 'credentials.json'](https://github.com/polius/Meteor/wiki/How-to-setup-'credentials.json')

### query_execution.py

[How to setup 'query_execution.py'](https://github.com/polius/Meteor/wiki/How-to-setup-'query_execution.py')

# 3. EXECUTION

Meteor has built-in three different modes:

### 3.1. Validation

Starts the Validation Process (Credentials, Queries, Regions).

```
$ python meteor.py --environment "environment_name" --validate [ credentials | queries | regions | all ]
```

### 3.2. Test Execution

Performs the Test Execution executing only SELECT queries.

```
$ python meteor.py --environment "environment_name" --test
```

### 3.3. Deployment Execution

Performs the Deployment executing ALL queries.

```
$ python meteor.py --environment "environment_name" --deploy
```

### Emergency Stop Button

To stop the Execution while is in process, use: **Ctrl+C**

# 4. RESULTS

## Meteor Web

Open the **meteor/web/index.html** with your web browser and import the generated execution file named **meteor.js** to see the execution results.

![](res/readme/meteor_web.png?raw=true)

## Slack Integration

![](res/readme/slack_header.png?raw=true)

![](res/readme/meteor_slack.png?raw=true)

# METEOR ARCHITECTURE

Here is a brief explanation about the tasks that Meteor performs during a deployment execution "--deploy". 

### 1) Validation

Before performing any action, a validation process is initiated reviewing:
- **Credentials**. Validates the "credentials.json" file.
- **Queries**. Validates the user-defined queries located in "query_execution.py".
- **Regions**. Validates all the SSH/SQL Connections. 

![](res/readme/1.validation.png?raw=true)

If all of the three steps are perfectly validated, Meteor continues its execution to the next phase. 

### 2) Deployment

In this phase the deployment process is started executing all queries.

![](res/readme/2.deployment.png?raw=true)

### 3) Logs

When the Deployment Execution is finished, Meteor retrieves all the logs created in all servers and starts a compilation process generating one single file named **meteor.js** which contains the result of all executions.

![](res/readme/3.logs.png?raw=true)

### 4) Summary

Meteor analyzes all the execution data and builds a Summary that is shown in the terminal.

![](res/readme/4.summary.png?raw=true)

### 5) Post Execution Tasks

![](res/readme/5.post_execution.png?raw=true)

To finish the process, 5 remaining tasks are executed:

- **AWS S3 Upload** (Optional). Uploads the execution logs to the AWS S3.
- **Clean Up**. Cleans all the temporary files generated during the Execution both Remote and Local Environments.
- **Slack** (Optional). Sends the Summary to an Slack Channel.
- **Execution Time**. Shows the Execution Time Summary.
- **Output**. Shows the generated Logs Path and the Logs Url.

# Under the Hood

The following graph shows the Meteor behaviour during a Deployment Process using the 3-Level Parallel Execution.

![](res/readme/meteor_architecture.png?raw=true)

# License

This project is licensed under the MIT license. See the [LICENSE](./LICENSE) file for more info.