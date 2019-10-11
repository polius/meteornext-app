![](https://raw.githubusercontent.com/polius/Meteor/master/res/readme/meteor_header.png)

[**credentials.json**](https://github.com/polius/Meteor/blob/master/app/credentials.json) is a JSON file that stores all the configuration and credentials needed by Meteor to work. 

**This file is divided by:**

[**1.  Environments**](https://github.com/polius/Meteor/wiki/How-to-setup-'credentials.json'#1-environments)

[**2.  Auxiliary Connections**](https://github.com/polius/Meteor/wiki/How-to-setup-'credentials.json'#2-auxiliary-connections)

[**3.  Slack**](https://github.com/polius/Meteor/wiki/How-to-setup-'credentials.json'#3-slack)

[**4.  Amazon S3**](https://github.com/polius/Meteor/wiki/How-to-setup-'credentials.json'#4-amazon-s3)

[**5.  Meteor Web**](https://github.com/polius/Meteor/wiki/How-to-setup-'credentials.json'#5-meteor-web)

[**6.  Execution Mode**](https://github.com/polius/Meteor/wiki/How-to-setup-'credentials.json'#6-execution-mode)

## 1. Environments

A required argument to start the Meteor app is the **environment** that will be used to start an execution process.

```
$ python meteor.py --environment "environment_name" ...
```

You can have set it up as many environments as you need. 

```
{
    "environments":
    {
        "PRODUCTION": [],
        "TEST": [],
        ...
     }
}
```

### Regions

One environment can have one or more **Regions**. In the next example we can see one environment named "PRODUCTION" with one region named "EU".

```
{
    "environments":
    {
        "PRODUCTION": 
        [
            {
                "region": "EU",
                "ssh": 
                {
                    "enabled": "False",
                    "hostname": "",
                    "username": "",
                    "password": "",
                    "key": "",
                    "deploy_path": ""
                },
                "sql": 
                [
                    {"name": "sql_server1", "hostname": "...", "username": "...", "password": "..."},
                    ...
                ]
            },
            ...
        ]
    }           
]
```

Regions have two elements: **SSH** and **SQL**.

#### SSH

In this section is defined the execution method that Meteor is going to use.

- **Cross-Region** Execution
- **Local** Execution

If this option is enabled, when the deployment starts Meteor copies itself and it's automatically deployed to the ssh defined host. Then performs all the sql executions from the deployed host.

If the option is disabled, Meteor is not deployed to any ssh host. It just performs all the sql executions from the host where is executed.

Here are the parameters needed to set it up:

```
"enabled": "" <-- "True" to enable it | "False" to disable it
"hostname": "" <-- The hostname used to perform the Cross-Region Execution
"username": "" <-- The username used to perform the Cross-Region Execution
"password": "" <-- If the host requires a password, else ""
"key": "" <-- If the host requires a private key enter the absolute path where this file is located (e.g: /home/ec2-user/.ssh/meteor.pem)
"deploy_path": "" <-- The absolute path where Meteor will be deployed (e.g: /home/ec2-user/meteor/)
```

#### SQL

In this section is configured all the SQL Servers that Meteor is going to perform the execution.

Every SQL Server is defined by:

```
{
    "name": "..." <-- A user-defined name that represents this server
    "hostname": "...",  <-- The hostname (IP/DNS)
    "username": "...", <-- The username
    "password": "..." <-- The password
}
```

#### In practical terms, what are the differences between Local & Cross-Region Executions?

Imagine that you had different SQL Servers in different zones cross the globe:

- SQL Server1, SQL Server2 (Europe)
- SQL Server3 (USA)
- SQL Server4, SQL Server5 (Japan)

If your Meteor application was located in Europe Region, the best configuration would be:

```
{
    "environments":
    {
        "PRODUCTION": 
        [
            {
                "region": "EU",
                "ssh": 
                {
                    "enabled": "False",
                    "hostname": "",
                    "username": "",
                    "password": "",
                    "key": "",
                    "deploy_path": ""
                },
                "sql": 
                [
                    {"name": "sql_server1", "hostname": "...", "username": "...", "password": "..."},
                    {"name": "sql_server2", "hostname": "...", "username": "...", "password": "..."}
                ]
            },
            {
                "region": "US",
                "ssh": 
                {
                    "enabled": "True",
                    "hostname": "...", <-- A server located in US Region
                    "username": "...",
                    "password": "...",
                    "key": "...",
                    "deploy_path": "..."
                },
                "sql": 
                [
                    {"name": "sql_server3", "hostname": "...", "username": "...", "password": "..."}
                ]
            },
            {
                "region": "JP",
                "ssh": 
                {
                    "enabled": "True",
                    "hostname": "...", <-- A server located in JP Region
                    "username": "...",
                    "password": "...",
                    "key": "...",
                    "deploy_path": "..."
                },
                "sql": 
                [
                    {"name": "sql_server4", "hostname": "...", "username": "...", "password": "..."},
                    {"name": "sql_server5", "hostname": "...", "username": "...", "password": "..."}
                ]
            },
        ]
    }
}
```

Using this configuration, the deployment will avoid transport delay executing all the queries between regions.

In this explained example, the python call to start a deployment execution would be:

```
$ python meteor.py --environment PRODUCTION --deploy
```

## 2. Auxiliary Connections

Auxiliary Connections stores SQL Connections that may come in handy during the execution process. 

```
"auxiliary_connections":
{
    "sql4":
    {
        "hostname": "", 
        "username": "",
        "password": ""
    },
    ...
}
```

To make it simple to understand, see the following example:

A Deployment is going to be executed in three servers: SQL1, SQL2 and SQL3.
Imagine the case where during the deployment would be the need to make a connection to a different server named SQL4  (server that is not included in the deployment process) to execute some queries:

```
- Deployment SQL1
- Deployment SQL2
-- Execute some queries to a different server SQL4
- Deployment SQL3
```

Here is where auxiliary connections comes into play.

## 3. Slack

[Slack](www.slack.com) is a cloud-based set of proprietary team collaboration tools and services.

To be notified everytime an execution finishes, enable the slack option.

```
"slack":
{
    "enabled": "", <-- "True" to enable it | "False" to disable it
    "webhook": "" <-- The webhook channel to send the notifications
}
```

## 4. Amazon S3

[Amazon S3](https://aws.amazon.com/s3/) or Amazon Simple Storage Service is a "simple storage service" offered by Amazon Web Services that provides object storage through a web service interface.

To upload all the execution logs to AWS S3, enable the S3 option.

```
"s3":
{
    "enabled": "", <-- "True" to enable it | "False" to disable it
    "aws_access_key_id": "", <-- Provided by AWS IAM
    "aws_secret_access_key": "", <-- Provided by AWS IAM
    "region_name": "", <-- The region name where the bucket is located (e.g: "eu-west-1")
    "bucket_name": "" <-- The bucket name to store the execution logs
}
```

## 5. Meteor Web

One of the most interesting features that Meteor has is the WebVisor (aka Meteor Web). This web application is used to analyze all the execution operations performed by Meteor.

![](https://raw.githubusercontent.com/polius/Meteor/master/res/readme/meteor_web.png)

This parameter is needed to generate an URL (to see all the execution results) everytime that a Meteor execution finishes.

Here is the configuration:

```
"web":
{
    "public_url": ""
}
```

Here is an example:

![](https://raw.githubusercontent.com/polius/Meteor/master/res/readme/logs_output.png)

```
"web":
{
    "public_url": "https://meteor.poliuscorp.com"
}
```

Another file that has to be configured also is the JS file: `/web/js/core.js`. A file used by the Meteor Web.

```
// ##############################################################################################
// Setup Variables
// ##############################################################################################
var resource_url = ""
```

Using the above example, this file should be:

```
// ##############################################################################################
// Setup Variables
// ##############################################################################################
var resource_url = "https://meteor.poliuscorp.com"
```

## 6. Execution Mode

Meteor is built to perform two types of executions modes.

*  **Sequential**: In this mode the execution is made sequentially per region, server and database.

```
"execution_mode":
{
    "parallel": "False",
    "threads": ""
}
```

While using this mode all the prints() used in the **query_execution.py** file are shown.
 
*  **Parallel**: In this mode the execution is performed in parallel per region and server. Furthermore Meteor opens X active threads per database.

```
"execution_mode":
{
    "parallel": "True",
    "threads": "X" <-- The number of active threads per database
}
```

While using this mode all the prints() used in the **query_execution.py** file are NOT shown.

The following graph shows how Meteor handles the Parallel Execution Mode.

![](https://raw.githubusercontent.com/polius/Meteor/master/res/readme/meteor_architecture.png)