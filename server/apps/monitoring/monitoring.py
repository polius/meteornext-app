import time
import datetime
import calendar
import requests
import threading
import json
from collections import OrderedDict

import connectors.base
import models.notifications

class Monitoring:
    def __init__(self, sql):
        self._sql = sql
        self._notifications = models.notifications.Notifications(sql)

    def monitor(self):
        # Get Monitoring Servers
        utcnow = self.__utcnow()
        query = """
            SELECT 
                s.id, s.name, s.engine, s.hostname, s.port, s.username, s.password,
                r.name AS 'rname', r.ssh_tunnel, r.hostname AS 'rhostname', r.port AS 'rport', r.username AS 'rusername', r.password AS 'rpassword', r.key,
                ms.available AS 'available', ms.summary, ms.parameters, SUM(m.monitor_enabled > 0) AS 'monitor_enabled', SUM(m.parameters_enabled > 0) AS 'parameters_enabled', SUM(m.processlist_enabled > 0) AS 'processlist_enabled', SUM(m.queries_enabled > 0) AS 'queries_enabled', IFNULL(MIN(mset.query_execution_time), 10) AS 'query_execution_time',
				ms.updated, IF(ms.updated IS NULL, 1, DATE_ADD(ms.updated, INTERVAL IFNULL(MIN(mset.monitor_interval), 10) SECOND) <= %s) AS 'needs_update'
            FROM monitoring m
			LEFT JOIN monitoring_servers ms ON ms.server_id = m.server_id
            LEFT JOIN monitoring_settings mset ON mset.user_id = m.user_id
            JOIN servers s ON s.id = m.server_id
            JOIN regions r ON r.id = s.region_id
			WHERE ms.updated IS NULL
            OR (m.processlist_enabled = 1 AND m.processlist_active = 1)
            OR m.queries_enabled = 1
            OR m.monitor_enabled = 1 
			OR m.parameters_enabled = 1
            GROUP BY m.server_id
            HAVING needs_update = 1;
        """
        servers_raw = self._sql.execute(query=query, args=(utcnow))

        # Build Servers List
        servers = []
        for s in servers_raw:
            server = {'ssh': {}, 'sql': {}}
            server['id'] = s['id']
            server['ssh'] = {'name': s['rname'], 'enabled': s['ssh_tunnel'], 'hostname': s['rhostname'], 'port': s['rport'], 'username': s['rusername'], 'password': s['rpassword'], 'key': s['key']}
            server['sql'] = {'name': s['name'], 'engine': s['engine'], 'hostname': s['hostname'], 'port': s['port'], 'username': s['username'], 'password': s['password']}
            server['monitor'] = {'available': s['available'], 'summary': s['summary'], 'parameters': s['parameters'], 'monitor_enabled': s['monitor_enabled'], 'parameters_enabled': s['parameters_enabled'], 'processlist_enabled': s['processlist_enabled'], 'queries_enabled': s['queries_enabled'], 'query_execution_time': s['query_execution_time'], 'updated': s['updated']}
            servers.append(server)

        # Get Server Info
        threads = []
        for s in servers:
            t = threading.Thread(target=self.__monitor_server, args=(s,))
            t.daemon = True
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def clean(self):
        utcnow = self.__utcnow()
        # Clean monitoring entries
        query = """
            DELETE m
            FROM monitoring m
            WHERE monitor_enabled = 0 
            AND parameters_enabled = 0
            AND processlist_enabled = 0
            AND queries_enabled = 0
        """
        self._sql.execute(query)

        query = """
            DELETE ms
            FROM monitoring_servers ms
            LEFT JOIN monitoring m ON m.server_id = ms.server_id 
            WHERE m.server_id IS NULL
        """
        self._sql.execute(query)

        # Clean monitoring events
        query = """
            DELETE FROM monitoring_events
            WHERE DATE_ADD(`time`, INTERVAL 31 DAY) < %s  
            FROM monitoring_events m
            WHERE monitor_enabled = 0 
            AND parameters_enabled = 0
            AND processlist_enabled = 0
            AND queries_enabled = 0
        """
        self._sql.execute(query, args=(utcnow))

        # Clean queries that exceeds the MAX defined data retention
        query = """
            DELETE q
            FROM monitoring_queries q
            LEFT JOIN
            (
                SELECT m.server_id, MAX(s.query_data_retention) AS 'data_retention'
                FROM monitoring_settings s
                JOIN monitoring m ON m.user_id = s.user_id
                GROUP BY m.server_id
            ) t ON t.server_id = q.server_id
            WHERE (t.server_id IS NULL AND DATE_ADD(q.first_seen, INTERVAL t.data_retention HOUR) <= %s)
            OR (t.server_id IS NOT NULL AND DATE_ADD(q.first_seen, INTERVAL 24 HOUR) <= %s);
        """
        self._sql.execute(query=query, args=(utcnow, utcnow))

    def __monitor_server(self, server):
        try:
            # Init Connection
            conn = None

            # If server is not available check connection every 15 seconds
            if server['monitor']['updated'] is not None:
                diff = (datetime.datetime.utcnow() - server['monitor']['updated']).total_seconds()
                if server['monitor']['available'] == 0 and diff < 15:
                    return

            # Start Connection
            conn = connectors.base.Base({'ssh': server['ssh'], 'sql': server['sql']})
            conn.connect()
        except Exception as e:
            # Monitoring Alarms
            self.__monitor_alarms(available=False, server=server, error=str(e))

            # Set server unavailable with error
            query = """
                INSERT INTO monitoring_servers (server_id, available, error, updated)
                VALUES (%s, 0, %s, %s)
                ON DUPLICATE KEY UPDATE
                    available = VALUES(available),
                    error = VALUES(error),
                    updated = VALUES(updated)
            """
            self._sql.execute(query=query, args=(server['id'], str(e), self.__utcnow()))
        else:
            # Get current timestamp in utc
            utcnow = self.__utcnow()

            # Build Parameters
            params = {}
            if server['monitor']['monitor_enabled'] or server['monitor']['parameters_enabled']:
                params = { p['Variable_name']: p['Value'] for p in conn.get_variables() }
                status = { s['Variable_name']: s['Value'] for s in conn.get_status() }

            # Build Processlist
            processlist = []
            if server['monitor']['monitor_enabled'] or server['monitor']['processlist_enabled'] or server['monitor']['queries_enabled']:
                processlist = conn.get_processlist()

            # Build Summary
            summary = {}
            if server['monitor']['monitor_enabled']:
                summary['info'] = {'version': params.get('version'), 'uptime': str(datetime.timedelta(seconds=int(status['Uptime']))), 'start_time': str((datetime.datetime.now() - datetime.timedelta(seconds=int(status['Uptime']))).replace(microsecond=0)), 'engine': server['sql']['engine'], 'sql_engine': params.get('default_storage_engine'), 'allocated_memory': params.get('innodb_buffer_pool_size'), 'time_zone': params.get('time_zone')}
                summary['logs'] = {'general_log': params.get('general_log'), 'general_log_file': params.get('general_log_file'), 'slow_log': params.get('slow_query_log'), 'slow_log_file': params.get('slow_query_log_file'), 'error_log_file': params.get('log_error')}
                summary['connections'] = {'current': status.get('Threads_connected'), 'max_connections_allowed': params.get('max_connections'), 'max_connections_reached': "{:.2f}%".format((int(status.get('Max_used_connections')) / int(params.get('max_connections'))) * 100), 'max_allowed_packet': params.get('max_allowed_packet'), 'transaction_isolation': params.get('tx_isolation'), 'bytes_received': status.get('Bytes_received'), 'bytes_sent': status.get('Bytes_sent')}
                summary['statements'] = {'all': status.get('Questions'), 'select': int(status.get('Com_select')) + int(status.get('Qcache_hits')), 'insert': int(status.get('Com_insert')) + int(status.get('Com_insert_select')), 'update': int(status.get('Com_update')) + int(status.get('Com_update_multi')), 'delete': int(status.get('Com_delete')) + int(status.get('Com_delete_multi'))}
                summary['index'] = {'percent': "{:.2f}%".format((int(status['Handler_read_rnd_next']) + int(status['Handler_read_rnd'])) / (int(status['Handler_read_rnd_next']) + int(status['Handler_read_rnd']) + int(status['Handler_read_first']) + int(status['Handler_read_next']) + int(status['Handler_read_key']) + int(status['Handler_read_prev']))), 'selects': status['Select_scan']}

            # Store Queries
            if server['monitor']['queries_enabled']:
                for i in processlist:
                    if i['TIME'] >= server['monitor']['query_execution_time'] and i['COMMAND'] in ['Query','Execute']:
                        query = """
                            INSERT INTO monitoring_queries (server_id, query_id, query_text, query_hash, db, user, host, first_seen, last_execution_time, max_execution_time, bavg_execution_time, avg_execution_time)
                            VALUES (%s, %s, %s, SHA1(%s), %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                user = VALUES(user),
                                host = VALUES(host),
                                bavg_execution_time = IF(count = 1 AND query_id = VALUES(query_id), VALUES(last_execution_time), IF(query_id = VALUES(query_id), bavg_execution_time, avg_execution_time)),
                                max_execution_time = GREATEST(max_execution_time, VALUES(last_execution_time)),
                                avg_execution_time = IF(count = 1 AND query_id = VALUES(query_id), VALUES(last_execution_time), IF(query_id = VALUES(query_id), (bavg_execution_time*(count-1) + VALUES(last_execution_time)) / count, (bavg_execution_time*count + VALUES(last_execution_time)) / (count+1))),
                                last_execution_time = VALUES(last_execution_time),
                                last_seen = %s,
                                count = IF(query_id = VALUES(query_id), count, count+1),
                                query_id = VALUES(query_id);
                        """
                        self._sql.execute(query=query, args=(server['id'], i['ID'], i['INFO'], i['INFO'], i['DB'], i['USER'], i['HOST'], utcnow, i['TIME'], i['TIME'], i['TIME'], i['TIME'], utcnow))

            # Monitoring Alarms
            self.__monitor_alarms(available=True, server=server, summary=summary, params=params, processlist=processlist)

            # Parse Variables
            summary = self.__dict2str(summary) if bool(summary) else ''
            params = self.__dict2str(params) if bool(params) else ''
            processlist = self.__dict2str(processlist) if len(processlist) > 0 else ''

            # Store Variables
            if summary != '' or params != '' or processlist != '':
                query = """
                    INSERT INTO monitoring_servers (server_id, available, summary, parameters, processlist, updated)
                    SELECT %s, 1, IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), %s
                    ON DUPLICATE KEY UPDATE
                        available = 1,
                        summary = COALESCE(VALUES(summary), summary),
                        parameters = COALESCE(VALUES(parameters), parameters),
                        processlist = COALESCE(VALUES(processlist), processlist),
                        updated = VALUES(updated)
                """
                self._sql.execute(query=query, args=(server['id'], summary, summary, params, params, processlist, processlist, utcnow))
        finally:
            # Stop Connection
            if conn:
                conn.stop()

    def __monitor_alarms(self, available, server, summary=None, params=None, processlist=None, error=None):
        # Init vars
        users = None
        slack = None

        # Check 'Unavailable'
        if server['monitor']['available'] == 1 and not available:
            notification = {
                'name': '{} has become unavailable'.format(server['sql']['name']),
                'status': 'ERROR',
                'icon': 'fas fa-circle',
                'category': 'monitoring',
                'data': '{{"id":"{}", "error":"{}"}}'.format(server['id'], error),
                'date': self.__utcnow(),
                'show': 1
            }
            self.__add_event(server_id=server['id'], status='unavailable', error=error)
            users = self.__get_users_server(server_id=server['id'])
            for user in users:
                self._notifications.post(user_id=user['user_id'], notification=notification)

            slack = self.__get_slack_server(server_id=server['id'])
            for s in slack:
                self.__slack(slack=s['monitor_slack_url'], server=server, mode=1, error=error)

        # Check 'Available'
        if server['monitor']['available'] == 0 and available:
            notification = {
                'name': '{} has become available'.format(server['sql']['name']),
                'status': 'SUCCESS',
                'icon': 'fas fa-circle',
                'category': 'monitoring',
                'data': '{{"id":"{}"}}'.format(server['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self.__add_event(server_id=server['id'], status='available')
            if users is None:
                users = self.__get_users_server(server_id=server['id'])
            for user in users:
                self._notifications.post(user_id=user['user_id'], notification=notification)

            if slack is None:
                slack = self.__get_slack_server(server_id=server['id'])
                for s in slack:
                    self.__slack(slack=s['monitor_slack_url'], server=server, mode=2, error=error)

        # Check 'Restarted'
        if server['monitor']['available'] == 1 and available and summary['info']['uptime'] < self.__str2dict(server['monitor']['summary'])['info']['uptime']:
            print("RESTARTED")
            print(self.__str2dict(server['monitor']['summary'])['info']['uptime'])
            print(summary['info']['uptime'])
            notification = {
                'name': '{} has restarted'.format(server['sql']['name']),
                'status': 'ERROR',
                'icon': 'fas fa-circle',
                'category': 'monitoring',
                'data': '{{"id":"{}"}}'.format(server['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self.__add_event(server_id=server['id'], status='restarted')
            if users is None:
                users = self.__get_users_server(server_id=server['id'])
            for user in users:
                self._notifications.post(user_id=user['user_id'], notification=notification)

            if slack is None:
                slack = self.__get_slack_server(server_id=server['id'])
                for s in slack:
                    self.__slack(slack=s['monitor_slack_url'], server=server, mode=1, error=error)

        # Check parameters
        # print(server['monitor']['parameters'])
        # print(params)

        # Check connections
        # print(processlist)

    def __slack(self, slack, server, mode, error):
        if mode == 1:
            name = '[Monitoring] {} has become unavailable'.format(server['sql']['name'])
        elif mode == 2:
            name = '[Monitoring] {} has become available'.format(server['sql']['name'])

        webhook_data = {
            "attachments": [
                {
                    "text": name,
                    "fields": [
                        {
                            "title": "Server",
                            "value": "```{}```".format(server['sql']['name']),
                            "short": False
                        },
                        {
                            "title": "Region",
                            "value": "```{}```".format(server['ssh']['name']),
                            "short": False
                        },
                        {
                            "title": "Hostname",
                            "value": "```{}```".format(server['sql']['hostname']),
                            "short": False
                        }
                    ],
                    "color": 'good' if error is None else 'danger',
                    "ts": calendar.timegm(time.gmtime())
                }
            ]
        }
        if error is not None:
            webhook_data['attachments'][0]['fields'].append({"title": "Error", "value": "```{}```".format(error), "short": False})

        # Send Slack Message
        response = requests.post(slack['webhook_url'], data=json.dumps(webhook_data), headers={'Content-Type': 'application/json'})
    
    def __get_users_server(self, server_id):
        query = "SELECT user_id FROM monitoring WHERE server_id = %s AND monitor_enabled = 1"
        return self._sql.execute(query=query, args=(server_id))

    def __get_slack_server(self, server_id):
        query = """
            SELECT DISTINCT ms.monitor_slack_url
            FROM monitoring_settings ms
            JOIN monitoring m ON m.user_id = ms.user_id AND m.server_id = %s
            WHERE ms.monitor_slack_enabled = 1
        """
        return self._sql.execute(query=query, args=(server_id))

    def __add_event(self, server_id, status, error=None):
        if status == 'unavailable':
            message = 'The server has become unavailable.'
            if error:
                message += '. Error: {}.'.format(error)
        elif status == 'available':
            message = 'The server has become available.'
        elif status == 'restarted':
            message = 'The server has restarted.'
            
        query = "INSERT INTO monitoring_events (`server_id`, `status`, `message`) VALUES (%s, %s, %s)"
        self._sql.execute(query=query, args=(server_id, status, message))

    def __dict2str(self, data):
        return json.dumps(data, separators=(',', ':'))

    def __str2dict(self, data):
        # Convert a string representation of a dictionary to a dictionary
        return json.loads(data, object_pairs_hook=OrderedDict)

    def __utcnow(self):
        # Get current timestamp in utc
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
