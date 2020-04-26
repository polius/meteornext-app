import json

class Monitoring_Queries:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user):
        query = """
            SELECT s.name AS 'server', q.query_id, q.query_text, q.db, q.user, q.host, q.first_seen, q.last_seen, q.execution_time, q.count
            FROM monitoring_queries q
            JOIN monitoring m ON m.server_id = q.server_id AND m.user_id = %s
            JOIN servers s ON s.id = q.server_id
            ORDER BY q.count DESC, q.execution_time DESC
            LIMIT 1000
        """
        return self._sql.execute(query, (user['id']))

    def filter(self, user, data):
        data = json.loads(data)
        keys = {i: data[i] for i in data if not i.endswith('_options') and len(data[i]) > 0}
        values = []
        filters = []
        for i in keys:
            if data[i+'_options'] == 'Equal':
                filters.append('AND q.{} = %s'.format(i))
                values.append(keys[i])
            elif data[i+'_options'] == 'Not equal':
                filters.append('AND q.{} != %s'.format(i))
                values.append(keys[i])
            elif data[i+'_options'] == 'Starts':
                filters.append('AND q.{} LIKE %s'.format(i))
                values.append(keys[i]+'%')
            elif data[i+'_options'] == 'Not starts':
                filters.append('AND q.{} NOT LIKE %s'.format(i))
                values.append(keys[i]+'%')

        # Filter by server
        filter_server = ''
        for i, k in enumerate(keys):
            if k == 'server':
                filter_server = filters[i].replace('AND q.server', 'AND s.name')
                del filters[i]
                values.insert(0, keys[k])
                del values[i+1]
                break

        query = """
            SELECT s.name AS 'server', q.query_id, q.query_text, q.db, q.user, q.host, q.first_seen, q.last_seen, q.execution_time, q.count
            FROM monitoring_queries q
            JOIN monitoring m ON m.server_id = q.server_id AND m.user_id = {}
            JOIN servers s ON s.id = q.server_id {}
            WHERE 1=1 {}
            ORDER BY q.count DESC, q.execution_time DESC
            LIMIT 1000
        """.format(user['id'], filter_server, ' '.join(filters))
        return self._sql.execute(query, (values))
