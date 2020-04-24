import json
import datetime
import threading
from collections import OrderedDict

from apps.monitoring.connector import connector

class Monitoring:
    def __init__(self, sql):
        self._sql = sql

    def start(self):
        # Get Monitoring Servers
        query = """
            SELECT 
                s.id, s.engine, s.hostname, s.port, s.username, s.password, s.aws_enabled, s.aws_instance_identifier, s.aws_region, s.aws_access_key_id, s.aws_secret_access_key,
                r.ssh_tunnel, r.hostname AS 'rhostname', r.port AS 'rport', r.username AS 'rusername', r.password AS 'rpassword', r.key,
                ms.summary, SUM(m.monitor_enabled > 0) AS 'monitor_enabled', SUM(m.parameters_enabled > 0) AS 'parameters_enabled', SUM(m.processlist_enabled > 0) AS 'processlist_enabled', SUM(m.queries_enabled > 0) AS 'queries_enabled'
            FROM monitoring m
			LEFT JOIN monitoring_servers ms ON ms.server_id = m.server_id
            JOIN servers s ON s.id = m.server_id
            JOIN regions r ON r.id = s.region_id
			WHERE ms.updated IS NULL
            OR (m.processlist_enabled = 1 AND m.processlist_active = 1)
            OR m.queries_enabled = 1
            OR ((m.monitor_enabled = 1 OR m.parameters_enabled = 1) AND DATE_ADD(ms.updated, INTERVAL (SELECT MIN(monitor_interval) FROM monitoring_settings WHERE user_id = m.user_id) SECOND) <= NOW())
            GROUP BY m.server_id
        """
        servers_raw = self._sql.execute(query)

        # Build Servers List
        servers = []
        for s in servers_raw:
            server = {'ssh': {}, 'sql': {}}
            server['id'] = s['id']
            server['ssh'] = {'enabled': s['ssh_tunnel'], 'hostname': s['hostname'], 'port': s['rport'], 'username': s['rusername'], 'password': s['rpassword'], 'key': s['key']}
            server['sql'] = {'engine': s['engine'], 'hostname': s['hostname'], 'port': s['port'], 'username': s['username'], 'password': s['password']}
            server['monitor'] = {'summary': s['summary'], 'monitor_enabled': s['monitor_enabled'], 'parameters_enabled': s['parameters_enabled'], 'processlist_enabled': s['processlist_enabled'], 'queries_enabled': s['queries_enabled']}
            servers.append(server)

        # Get Server Info
        threads = []
        for s in servers:
            t = threading.Thread(target=self.__start_server, args=(s,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def clean(self):
        # Clean Monitoring Servers
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

    def __start_server(self, server):
        if server['sql']['engine'] == 'MySQL':
            self.__start_server_mysql(server)

    def __start_server_mysql(self, server):
        try:
            # Start Connection
            conn = connector(server)
            conn.start()
        except Exception:
            # Set Server Available to False
            query = """
                INSERT INTO monitoring_servers (server_id, summary, updated)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE
                    summary = VALUES(summary),
                    updated = VALUES(updated)
            """
            if server['monitor']['summary'] is None:
                summary = {'info': {'available': False}}
            else:
                summary = self.__str2dict(server['monitor']['summary'])
                summary['info']['available'] = False
            self._sql.execute(query=query, args=(server['id'], self.__dict2str(summary)))
        else:
            # Build Parameters
            params = ''
            if server['monitor']['monitor_enabled'] or server['monitor']['parameters_enabled']:
                params = { p['Variable_name']: p['Value'] for p in conn.get_parameters() }
                status = { s['Variable_name']: s['Value'] for s in conn.get_status() }

            # Build Processlist
            processlist = ''
            if server['monitor']['monitor_enabled'] or server['monitor']['processlist_enabled']:
                processlist = conn.get_processlist()
            
            # Build Summary
            summary = ''
            if server['monitor']['monitor_enabled']:
                summary = {'info': {}, 'logs': {}, 'connections': {}, 'statements': {}, 'index': {}, 'rds': {}}
                summary['info'] = {'available': True, 'version': params.get('version'), 'uptime': str(datetime.timedelta(seconds=int(status['Uptime']))), 'start_time': str((datetime.datetime.now() - datetime.timedelta(seconds=int(status['Uptime']))).replace(microsecond=0)), 'engine': server['sql']['engine'], 'sql_engine': params.get('default_storage_engine'), 'allocated_memory': params.get('innodb_buffer_pool_size'), 'time_zone': params.get('time_zone')}
                summary['logs'] = {'general_log': params.get('general_log'), 'general_log_file': params.get('general_log_file'), 'slow_log': params.get('slow_query_log'), 'slow_log_file': params.get('slow_query_log_file'), 'error_log_file': params.get('log_error')}
                summary['connections'] = {'current': status.get('Threads_connected'), 'max_connections_allowed': params.get('max_connections'), 'max_connections_reached': "{:.2f}%".format((int(status.get('Max_used_connections')) / int(params.get('max_connections'))) * 100), 'max_allowed_packet': params.get('max_allowed_packet'), 'transaction_isolation': params.get('tx_isolation'), 'bytes_received': status.get('Bytes_received'), 'bytes_sent': status.get('Bytes_sent')}
                summary['statements'] = {'all': status.get('Questions'), 'select': int(status.get('Com_select')) + int(status.get('Qcache_hits')), 'insert': int(status.get('Com_insert')) + int(status.get('Com_insert_select')), 'update': int(status.get('Com_update')) + int(status.get('Com_update_multi')), 'delete': int(status.get('Com_delete')) + int(status.get('Com_delete_multi'))}
                summary['index'] = {'percent': "{:.2f}%".format((int(status['Handler_read_rnd_next']) + int(status['Handler_read_rnd'])) / (int(status['Handler_read_rnd_next']) + int(status['Handler_read_rnd']) + int(status['Handler_read_first']) + int(status['Handler_read_next']) + int(status['Handler_read_key']) + int(status['Handler_read_prev']))), 'selects': status['Select_scan']}
                summary['rds'] = {}

            # Parse Variables
            summary = self.__dict2str(summary) if summary != '' else ''
            params = self.__dict2str(params) if params != '' else ''
            processlist = self.__dict2str(processlist) if processlist != '' else ''

            # Store Variables
            query = """
                INSERT INTO monitoring_servers (server_id, summary, parameters, processlist, updated)
                SELECT %s, IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), IF(%s = '', NULL, %s), CURRENT_TIMESTAMP
                ON DUPLICATE KEY UPDATE
                    summary = VALUES(summary),
                    parameters = VALUES(parameters),
                    processlist = VALUES(processlist),
                    updated = VALUES(updated)
            """
            self._sql.execute(query=query, args=(server['id'], summary, summary, params, params, processlist, processlist))

        finally:
            # Stop Connection
            conn.stop()

    def __dict2str(self, data):
        return json.dumps(data, separators=(',', ':'))

    def __str2dict(self, data):
        # Convert a string representation of a dictionary to a dictionary
        return json.loads(data, object_pairs_hook=OrderedDict)
