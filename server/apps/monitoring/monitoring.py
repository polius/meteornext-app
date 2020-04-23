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
            m.summary 
        FROM monitoring m
        JOIN servers s ON s.id = m.server_id
        JOIN regions r ON r.id = s.region_id
        LEFT JOIN monitoring_settings ms ON ms.group_id = r.group_id AND ms.name = 'interval'
        WHERE m.updated IS NULL
        OR (ms.value IS NULL AND DATE_ADD(m.updated, INTERVAL 10 SECOND) <= NOW())
		OR (ms.value IS NOT NULL AND DATE_ADD(m.updated, INTERVAL ms.value SECOND) <= NOW())
        """
        servers_raw = self._sql.execute(query)

        # Build Servers List
        servers = []
        for s in servers_raw:
            server = {'ssh': {}, 'sql': {}}
            server['id'] = s['id']
            server['ssh'] = {'enabled': s['ssh_tunnel'], 'hostname': s['hostname'], 'port': s['rport'], 'username': s['rusername'], 'password': s['rpassword'], 'key': s['key']}
            server['sql'] = {'engine': s['engine'], 'hostname': s['hostname'], 'port': s['port'], 'username': s['username'], 'password': s['password']}
            server['summary'] = s['summary']
            servers.append(server)

        # Get Server Info
        threads = []
        for s in servers:
            t = threading.Thread(target=self.__start_server, args=(s,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

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
            if server['summary'] is None:
                summary = {'info': {'available': False}}
                query = "UPDATE monitoring SET summary = %s, updated = CURRENT_TIMESTAMP WHERE server_id = %s"
            else:
                summary = self.__str2dict(server['summary'])
                summary['info']['available'] = False
                query = "UPDATE monitoring SET summary = %s, updated = CURRENT_TIMESTAMP WHERE server_id = %s"
            self._sql.execute(query=query, args=(self.__dict2str(summary), server['id']))
        else:
            # Get Server Info
            params = conn.get_parameters()
            status = conn.get_status()
            processlist = conn.get_processlist()
            params = { p['Variable_name']: p['Value'] for p in params }
            status = { s['Variable_name']: s['Value'] for s in status }

            # Build Summary
            summary = {'info': {}, 'logs': {}, 'connections': {}, 'statements': {}, 'index': {}, 'rds': {}}
            summary['info'] = {'available': True, 'version': params.get('version'), 'uptime': str(datetime.timedelta(seconds=int(status['Uptime']))), 'start_time': str((datetime.datetime.now() - datetime.timedelta(seconds=int(status['Uptime']))).replace(microsecond=0)), 'engine': server['sql']['engine'], 'sql_engine': params.get('default_storage_engine'), 'allocated_memory': params.get('innodb_buffer_pool_size'), 'time_zone': params.get('time_zone')}
            summary['logs'] = {'general_log': params.get('general_log'), 'general_log_file': params.get('general_log_file'), 'slow_log': params.get('slow_query_log'), 'slow_log_file': params.get('slow_query_log_file'), 'error_log_file': params.get('log_error')}
            summary['connections'] = {'current': status.get('Threads_connected'), 'max_connections_allowed': params.get('max_connections'), 'max_connections_reached': "{:.2f}%".format((int(status.get('Max_used_connections')) / int(params.get('max_connections'))) * 100), 'max_allowed_packet': params.get('max_allowed_packet'), 'transaction_isolation': params.get('tx_isolation'), 'bytes_received': status.get('Bytes_received'), 'bytes_sent': status.get('Bytes_sent')}
            summary['statements'] = {'all': status.get('Questions'), 'select': int(status.get('Com_select')) + int(status.get('Qcache_hits')), 'insert': int(status.get('Com_insert')) + int(status.get('Com_insert_select')), 'update': int(status.get('Com_update')) + int(status.get('Com_update_multi')), 'delete': int(status.get('Com_delete')) + int(status.get('Com_delete_multi'))}
            summary['index'] = {'percent': "{:.2f}%".format((int(status['Handler_read_rnd_next']) + int(status['Handler_read_rnd'])) / (int(status['Handler_read_rnd_next']) + int(status['Handler_read_rnd']) + int(status['Handler_read_first']) + int(status['Handler_read_next']) + int(status['Handler_read_key']) + int(status['Handler_read_prev']))), 'selects': status['Select_scan']}
            summary['rds'] = {}

            # Store Variables
            query = """
                UPDATE monitoring
                SET summary = %s,
                    parameters = %s,
                    processlist = %s,
                    updated = CURRENT_TIMESTAMP
                WHERE server_id = %s
            """
            self._sql.execute(query=query, args=(self.__dict2str(summary), self.__dict2str(params), self.__dict2str(processlist), server['id']))

        finally:
            # Stop Connection
            conn.stop()

    def __dict2str(self, data):
        return json.dumps(data, separators=(',', ':'))

    def __str2dict(self, data):
        # Convert a string representation of a dictionary to a dictionary
        return json.loads(data, object_pairs_hook=OrderedDict)
