import os
import time
import json
import calendar
import requests
import threading
from datetime import datetime, timedelta
from statistics import median
from collections import OrderedDict

import connectors.base
import models.notifications

class Monitor:
    def __init__(self, license, sql):
        self._license = license
        self._sql = sql

    def start(self):
        self.__start_monitor()

    ####################
    # Internal Methods #
    ####################
    def __start_monitor(self):
        # Init SQL Connection
        conn = connectors.base.Base(self._sql)

        # Get Monitoring Servers
        query = """
            SELECT
                s.id, s.name, s.engine, s.hostname, s.port, s.username, s.password, s.ssl, s.ssl_client_key, s.ssl_client_certificate, s.ssl_ca_certificate, s.ssl_verify_ca,
                r.name AS 'rname', r.ssh_tunnel, r.hostname AS 'rhostname', r.port AS 'rport', r.username AS 'rusername', r.password AS 'rpassword', r.key,
                ms.available AS 'available', ms.summary, ms.parameters, SUM(m.monitor_enabled > 0) AS 'monitor_enabled', SUM(m.parameters_enabled > 0) AS 'parameters_enabled', SUM(m.processlist_enabled > 0) AS 'processlist_enabled', SUM(m.queries_enabled > 0) AS 'queries_enabled', IFNULL(MIN(mset.query_execution_time), 10) AS 'query_execution_time',
                ms.updated
            FROM monitoring m
            LEFT JOIN monitoring_servers ms ON ms.server_id = m.server_id
            LEFT JOIN monitoring_settings mset ON mset.user_id = m.user_id
            JOIN users u ON u.id = m.user_id AND u.disabled = 0
            JOIN groups g ON g.id = u.group_id
            JOIN servers s ON s.id = m.server_id AND s.usage LIKE '%%M%%'
            JOIN regions r ON r.id = s.region_id
            WHERE (
                (m.processlist_enabled = 1 AND m.processlist_active = 1)
                OR m.queries_enabled = 1
                OR m.monitor_enabled = 1
                OR m.parameters_enabled = 1
            )
            AND IF(ms.updated IS NULL, 1, TIMESTAMPDIFF(SECOND, ms.updated, %s) >= g.monitoring_interval) = 1
            GROUP BY m.server_id
        """
        servers_raw = conn.execute(query=query, args=(self.__utcnow()))

        # Close SQL Connection
        conn.stop()

        # Build Servers List
        servers = []
        for s in servers_raw:
            server = {'ssh': {}, 'sql': {}}
            server['id'] = s['id']
            server['ssh'] = {'name': s['rname'], 'enabled': s['ssh_tunnel'], 'hostname': s['rhostname'], 'port': s['rport'], 'username': s['rusername'], 'password': s['rpassword'], 'key': s['key']}
            server['sql'] = {'name': s['name'], 'engine': s['engine'], 'hostname': s['hostname'], 'port': s['port'], 'username': s['username'], 'password': s['password'], 'ssl': s['ssl'], 'ssl_client_key': s['ssl_client_key'], 'ssl_client_certificate': s['ssl_client_certificate'], 'ssl_ca_certificate': s['ssl_ca_certificate'], 'ssl_verify_ca': s['ssl_verify_ca']}
            server['monitor'] = {'available': s['available'], 'summary': s['summary'], 'parameters': s['parameters'], 'monitor_enabled': s['monitor_enabled'], 'parameters_enabled': s['parameters_enabled'], 'processlist_enabled': s['processlist_enabled'], 'queries_enabled': s['queries_enabled'], 'query_execution_time': s['query_execution_time'], 'updated': s['updated']}
            servers.append(server)

        # Start Monitoring
        servers_split = list(self.__split(servers, os.cpu_count()))
        threads = []
        for servers_chunk in servers_split:
            if len(servers_chunk) != 0:
                t = threading.Thread(target=self.__monitor_servers, args=(servers_chunk,))
                threads.append(t)
                t.start()

        # Wait Threads to Finish
        try:
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            pass

    def __split(self, a, n):
        k, m = divmod(len(a), n)
        return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

    def __monitor_servers(self, servers):
        for server in servers:
            self.__monitor_server(server)

    def __monitor_server(self, server):
        try:
            # If server is not available check connection every 30 seconds
            if server['monitor']['updated'] is not None:
                diff = (datetime.utcnow() - server['monitor']['updated']).total_seconds()
                if server['monitor']['available'] == 0 and diff < 30:
                    return

            # Start Connection
            conn = connectors.base.Base({'ssh': server['ssh'], 'sql': server['sql']})
            conn.connect()

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
                summary['info'] = {'version': params.get('version'), 'raw_uptime': status['Uptime'], 'uptime': str(timedelta(seconds=int(status['Uptime']))), 'start_time': str((datetime.now() - timedelta(seconds=int(status['Uptime']))).replace(microsecond=0)), 'engine': server['sql']['engine'], 'sql_engine': params.get('default_storage_engine'), 'allocated_memory': params.get('innodb_buffer_pool_size'), 'time_zone': params.get('time_zone')}
                summary['logs'] = {'general_log': params.get('general_log'), 'general_log_file': params.get('general_log_file'), 'slow_log': params.get('slow_query_log'), 'slow_log_file': params.get('slow_query_log_file'), 'error_log_file': params.get('log_error')}
                summary['connections'] = {'current': status.get('Threads_connected'), 'max_connections_allowed': params.get('max_connections'), 'max_connections_reached': "{:.2f}%".format((int(status.get('Max_used_connections')) / int(params.get('max_connections'))) * 100), 'max_allowed_packet': params.get('max_allowed_packet'), 'transaction_isolation': params.get('tx_isolation') or params.get('transaction_isolation'), 'bytes_received': status.get('Bytes_received'), 'bytes_sent': status.get('Bytes_sent')}
                summary['statements'] = {'select': int(status.get('Com_select')), 'insert': int(status.get('Com_insert')) + int(status.get('Com_insert_select')), 'update': int(status.get('Com_update')) + int(status.get('Com_update_multi')), 'delete': int(status.get('Com_delete')) + int(status.get('Com_delete_multi'))}
                summary['statements']['all'] = summary['statements']['select'] + summary['statements']['insert'] + summary['statements']['update'] + summary['statements']['delete']
                summary['index'] = {'percent': "{:.2f}%".format((int(status['Handler_read_rnd_next']) + int(status['Handler_read_rnd'])) / (int(status['Handler_read_rnd_next']) + int(status['Handler_read_rnd']) + int(status['Handler_read_first']) + int(status['Handler_read_next']) + int(status['Handler_read_key']) + int(status['Handler_read_prev']))), 'selects': status['Select_scan']}

            # Stop Connection
            conn.stop()

            # Start Connection
            conn = connectors.base.Base(self._sql)

            # Store Queries
            if server['monitor']['queries_enabled']:
                for i in processlist:
                    if i['TIME'] >= server['monitor']['query_execution_time'] and i['COMMAND'] in ['Query','Execute']:
                        db = '' if i['DB'] is None else i['DB']
                        query = """
                            INSERT INTO monitoring_queries (server_id, query_id, query_text, query_hash, db, user, host, first_seen, last_seen, last_execution_time, max_execution_time, bavg_execution_time, avg_execution_time)
                            VALUES (%s, %s, %s, SHA1(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        conn.execute(query=query, args=(server['id'], i['ID'], i['INFO'], i['INFO'], db, i['USER'], i['HOST'], utcnow, utcnow, i['TIME'], i['TIME'], i['TIME'], i['TIME'], utcnow))

            # Monitoring Alarms
            if server['monitor']['monitor_enabled'] == 1:
                self.__monitor_alarms(conn, available=True, server=server, summary=summary, params=params, processlist=processlist)

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
                        available = VALUES(available),
                        summary = COALESCE(VALUES(summary), summary),
                        parameters = COALESCE(VALUES(parameters), parameters),
                        processlist = COALESCE(VALUES(processlist), processlist),
                        error = NULL,
                        updated = VALUES(updated)
                """
                conn.execute(query=query, args=(server['id'], summary, summary, params, params, processlist, processlist, utcnow))

            # Close SQL Connection
            conn.stop()

        except Exception as e:
            try:
                # Start Connection
                conn = connectors.base.Base(self._sql)

                # Monitoring Alarms
                if server['monitor']['monitor_enabled'] == 1:
                    self.__monitor_alarms(conn, available=False, server=server, error=str(e))

                # Set server unavailable with error
                query = """
                    INSERT INTO monitoring_servers (server_id, available, error, updated)
                    VALUES (%s, 0, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        available = VALUES(available),
                        error = VALUES(error),
                        updated = VALUES(updated)
                """
                conn.execute(query=query, args=(server['id'], str(e), self.__utcnow()))
            finally:
                # Close SQL Connection
                conn.stop()

    def __monitor_alarms(self, conn, available, server, summary={}, params={}, processlist=[], error=None):
        # Init vars
        notifications = models.notifications.Notifications(conn)
        users = None
        slack = None

        # Check 'Unavailable'
        if (server['monitor']['available'] is None and error is not None) or (server['monitor']['available'] is not None and int(server['monitor']['available']) == 1 and not available):
            notification = {
                'name': f"Server '{server['sql']['name']}' has become unavailable.",
                'status': 'ERROR',
                'category': 'monitoring',
                'data': '{{"id":"{}"}}'.format(server['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self.__add_event(conn, server_id=server['id'], event='unavailable', data=error)
            users = self.__get_users_server(conn, server_id=server['id'])
            for user in users:
                notifications.post(user_id=user['user_id'], notification=notification)

            slack = self.__get_slack_server(conn, server_id=server['id'])
            for s in slack:
                self.__slack(slack=s, server=server, event='unavailable', data=error)

        # Check 'Available'
        if server['monitor']['available'] is not None and int(server['monitor']['available']) == 0 and available:
            notification = {
                'name': f"Server '{server['sql']['name']}' has become available.",
                'status': 'SUCCESS',
                'category': 'monitoring',
                'data': '{{"id":"{}"}}'.format(server['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self.__add_event(conn, server_id=server['id'], event='available')
            if users is None:
                users = self.__get_users_server(conn, server_id=server['id'])
            for user in users:
                notifications.post(user_id=user['user_id'], notification=notification)

            if slack is None:
                slack = self.__get_slack_server(conn, server_id=server['id'])
            for s in slack:
                self.__slack(slack=s, server=server, event='available', data=None)

        # Check 'Restarted'
        info = None if server['monitor']['summary'] is None else self.__str2dict(server['monitor']['summary'])['info']
        if summary and info and int(summary['info']['raw_uptime']) < int(info['raw_uptime']):
            notification = {
                'name': f"Server '{server['sql']['name']}' has restarted.",
                'status': 'WARNING',
                'category': 'monitoring',
                'data': '{{"id":"{}"}}'.format(server['id']),
                'date': self.__utcnow(),
                'show': 1
            }
            self.__add_event(conn, server_id=server['id'], event='restarted')
            if users is None:
                users = self.__get_users_server(conn, server_id=server['id'])
            for user in users:
                notifications.post(user_id=user['user_id'], notification=notification)

            data = {'previous_uptime': info['uptime'], 'previous_start_time': info['start_time'], 'current_uptime': summary['info']['uptime'], 'current_start_time': summary['info']['start_time']}
            if slack is None:
                slack = self.__get_slack_server(conn, server_id=server['id'])
            for s in slack:
                self.__slack(slack=s, server=server, event='restarted', data=data)

        # Check parameters
        if server['monitor']['parameters'] and available:
            origin = self.__str2dict(server['monitor']['parameters'])
            diff = { k : params[k] for k, _ in set(params.items()) - set(origin.items())}
            if len(diff) > 0 and not (len(diff) == 1 and 'innodb_thread_sleep_delay' in diff):
                data = { k: {"previous": origin[k] if k in origin else '', "current":v} for k,v in diff.items() }
                notification = {
                    'name': f"Server '{server['sql']['name']}' has parameters changed.",
                    'status': 'INFO',
                    'category': 'monitoring',
                    'data': '{{"id":"{}"}}'.format(server['id']),
                    'date': self.__utcnow(),
                    'show': 1
                }
                self.__add_event(conn, server_id=server['id'], event='parameters', data=self.__dict2str(data))
                if users is None:
                    users = self.__get_users_server(conn, server_id=server['id'])
                for user in users:
                    notifications.post(user_id=user['user_id'], notification=notification)

                if slack is None:
                    slack = self.__get_slack_server(conn, server_id=server['id'])
                for s in slack:
                    self.__slack(slack=s, server=server, event='parameters', data=data)

        # Check connections
        connections = None if server['monitor']['summary'] is None else self.__str2dict(server['monitor']['summary'])['connections']
        if server['monitor']['available'] == 1 and available:
            last_event = self.__get_last_event(conn, server['id'])
            queries = [int(i['TIME']) for i in processlist if i['COMMAND'] in ['Query','Execute']]
            queries.sort(reverse=True)
            event = ''
            # Connections - Critical [+100 connections. 3 top median >= 300 seconds. 5 top avg >= 300]
            if (len(last_event) == 0 or last_event[0]['event'] != 'connections_critical' or (last_event[0]['event'] == 'connections_critical' and last_event[0]['time'] + timedelta(minutes=1) < datetime.utcnow())) and len(queries) >= 100 and median(queries[:3]) >= 300 and sum(queries[:5])/5 >= 300:
                notification_name = 'Server \'{}\' Critical | {} Connections.'.format(server['sql']['name'], len(queries))
                notification_status = 'ERROR'
                event = 'connections_critical'
            # Connections - Warning [+ 50 connections. 3 top median >= 60 seconds. 5 top avg >= 60]
            elif (len(last_event) == 0 or last_event[0]['event'] == 'connections_stable' or (last_event[0]['event'] == 'connections_critical' and last_event[0]['time'] + timedelta(minutes=1) < datetime.utcnow() and len(queries) < int(connections['current']))) and len(queries) >= 50 and median(queries[:3]) >= 60 and sum(queries[:5])/5 >= 60:
                notification_name = 'Server \'{}\' Warning | {} Connections.'.format(server['sql']['name'], len(queries))
                notification_status = 'WARNING'
                event = 'connections_warning'
            # Connections - Stable [- 20 connections]
            elif len(last_event) != 0 and last_event[0]['event'] in ['connections_warning','connections_critical'] and len(queries) < 20:
                notification_name = 'Server \'{}\' Stable | {} Connections.'.format(server['sql']['name'], len(queries))
                notification_status = 'SUCCESS'
                event = 'connections_stable'

            if event != '': 
                notification = {
                    'name': notification_name,
                    'status': notification_status,
                    'category': 'monitoring',
                    'data': '{{"id":"{}"}}'.format(server['id']),
                    'date': self.__utcnow(),
                    'show': 1
                }
                self.__add_event(conn, server_id=server['id'], event=event, data=len(queries))
                if users is None:
                    users = self.__get_users_server(conn, server_id=server['id'])
                for user in users:
                    notifications.post(user_id=user['user_id'], notification=notification)
                if slack is None:
                    slack = self.__get_slack_server(conn, server_id=server['id'])
                for s in slack:
                    self.__slack(slack=s, server=server, event=event, data=len(queries))

    def __slack(self, slack, server, event, data):
        if event == 'unavailable':
            name = '[{}] Server has become unavailable'.format(server['sql']['name'])
        elif event == 'available':
            name = '[{}] Server has become available'.format(server['sql']['name'])
        elif event == 'restarted':
            name = '[{}] Server has restarted'.format(server['sql']['name'])
        elif event == 'parameters':
            name = '[{}] Server configuration change detected'.format(server['sql']['name'])
        elif event == 'connections_critical':
            name = '[{}] Server Critical | Current Connections: {}'.format(server['sql']['name'], data)
        elif event == 'connections_warning':
            name = '[{}] Server Warning | Current Connections: {}'.format(server['sql']['name'], data)
        elif event == 'connections_stable':
            name = '[{}] Server Stable | Current Connections: {}'.format(server['sql']['name'], data)

        webhook_data = {
            "text": "{}".format(name),
            "attachments": [
                {
                    "fields": [
                        {
                            "title": "Information",
                            "value": "```{}/monitor/{}```".format(slack['monitor_base_url'], server['id']),
                            "short": False
                        }
                    ],
                    "color": 'good' if event in ['available','connections_stable'] else 'warning' if event in ['restarted','connections_warning'] else '#3e9cef' if event == 'parameters' else 'danger',
                    "ts": calendar.timegm(time.gmtime())
                }
            ]
        }
        if event == 'unavailable':
            webhook_data['attachments'][0]['fields'].append({"title": "Error", "value": "```{}```".format(data), "short": False})
        elif event == 'parameters':
            for key, value in data.items():
                webhook_data['attachments'][0]['fields'].append({"title": "Variable Name", "value": "`{}`".format(key), "short": False})
                webhook_data['attachments'][0]['fields'].append({"title": "Previous Value", "value": value['previous'], "short": True})
                webhook_data['attachments'][0]['fields'].append({"title": "Current Value", "value": value['current'], "short": True})
        elif event == 'restarted':
            webhook_data['attachments'][0]['fields'].append({"title": "Previous Uptime", "value": data['previous_uptime'], "short": True})
            webhook_data['attachments'][0]['fields'].append({"title": "Previous Start Time", "value": data['previous_start_time'], "short": True})
            webhook_data['attachments'][0]['fields'].append({"title": "Current Uptime", "value": data['current_uptime'], "short": True})
            webhook_data['attachments'][0]['fields'].append({"title": "Current Start Time", "value": data['current_start_time'], "short": True})
        # Send Slack Message
        requests.post(slack['monitor_slack_url'], data=json.dumps(webhook_data), headers={'Content-Type': 'application/json'})
    
    def __get_users_server(self, conn, server_id):
        query = """
            SELECT m.user_id
            FROM monitoring m
            JOIN (
                SELECT
                    u.id AS 'user_id',
                    s.id AS 'server_id',
                    IF(@usr != u.id, @cnt := 0, @cnt := @cnt) AS 'logic1',
                    IF(%(resources)s = -1 OR (@cnt := @cnt + 1) <= %(resources)s, 1, 0) AS 'active',
                    @usr := u.id AS 'logic2'
                FROM users u
                JOIN (SELECT @cnt := 0, @usr := 0) t
                JOIN servers s ON s.group_id = u.group_id AND (s.shared = 1 OR s.owner_id = u.id)
                ORDER BY u.id, s.id
            ) t ON t.user_id = m.user_id AND t.server_id = m.server_id
            WHERE m.server_id = %(server_id)s
            AND m.monitor_enabled = 1
            AND t.active = 1
        """
        return conn.execute(query=query, args={"server_id": server_id, "resources": self._license.get_resources()})

    def __get_slack_server(self, conn, server_id):
        query = """
            SELECT DISTINCT ms.monitor_slack_url, ms.monitor_base_url
            FROM monitoring_settings ms
            JOIN monitoring m ON m.user_id = ms.user_id AND m.server_id = %(server_id)s
            JOIN (
                SELECT
                    u.id AS 'user_id',
                    s.id AS 'server_id',
                    IF(@usr != u.id, @cnt := 0, @cnt := @cnt) AS 'logic1',
                    IF(%(resources)s = -1 OR (@cnt := @cnt + 1) <= %(resources)s, 1, 0) AS 'active',
                    @usr := u.id AS 'logic2'
                FROM users u
                JOIN (SELECT @cnt := 0, @usr := 0) t
                JOIN servers s ON s.group_id = u.group_id AND (s.shared = 1 OR s.owner_id = u.id)
                ORDER BY u.id, s.id
            ) t ON t.user_id = m.user_id AND t.server_id = m.server_id
            WHERE ms.monitor_slack_enabled = 1
            AND t.active = 1
        """
        return conn.execute(query=query, args={"server_id": server_id, "resources": self._license.get_resources()})

    def __get_last_event(self, conn, server_id):
        query = """
            SELECT event, time
            FROM monitoring_events
            WHERE server_id = %s
            AND event IN ('connections_critical','connections_warning','connections_stable')
            ORDER BY id DESC
            LIMIT 1
        """
        return conn.execute(query=query, args=(server_id))

    def __add_event(self, conn, server_id, event, data=None):
        query = "INSERT INTO monitoring_events (`server_id`, `event`, `data`, `time`) VALUES (%s, %s, %s, %s)"
        conn.execute(query=query, args=(server_id, event, data, self.__utcnow()))

    def __dict2str(self, data):
        return json.dumps(data, separators=(',', ':'))

    def __str2dict(self, data):
        # Convert a string representation of a dictionary to a dictionary
        return json.loads(data, object_pairs_hook=OrderedDict)

    def __utcnow(self):
        # Get current timestamp in utc
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
