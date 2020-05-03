class Monitoring_Queries:
    def __init__(self, sql):
        self._sql = sql

    def get(self, user, filters=None, sort=None):
        if not filters and not sort:
            query = """
                SELECT s.name AS 'server', q.query_text, q.db, q.user, q.host, q.first_seen, q.last_seen, q.last_execution_time, q.max_execution_time, q.avg_execution_time, q.count
                FROM monitoring_queries q
                JOIN monitoring m ON m.server_id = q.server_id AND m.user_id = %s
                JOIN servers s ON s.id = q.server_id
                ORDER BY q.count DESC, q.avg_execution_time DESC
                LIMIT 1000
            """
            return self._sql.execute(query, (user['id']))
        else:
            # Apply filters
            keys = {i: filters[i] for i in filters if not i.endswith('_options') and len(filters[i]) > 0}
            values = []
            filters_values = []
            for i in keys:
                if filters[i+'_options'] == 'Equal':
                    filters_values.append('AND q.{} = %s'.format(i))
                    values.append(keys[i])
                elif filters[i+'_options'] == 'Not equal':
                    filters_values.append('AND q.{} != %s'.format(i))
                    values.append(keys[i])
                elif filters[i+'_options'] == 'Starts':
                    filters_values.append('AND q.{} LIKE %s'.format(i))
                    values.append(keys[i]+'%')
                elif filters[i+'_options'] == 'Not starts':
                    filters_values.append('AND q.{} NOT LIKE %s'.format(i))
                    values.append(keys[i]+'%')

            # - Filter by server -
            filter_server = ''
            for i, k in enumerate(keys):
                if k == 'server':
                    filter_server = filters_values[i].replace('AND q.server', 'AND s.name')
                    del filters_values[i]
                    values.insert(0, keys[k])
                    del values[i+1]
                    break

            # Apply sort
            order_by = []
            if len(sort) == 0:
                order_by.append('q.count DESC, q.last_execution_time DESC')
            else:
                for i, s in enumerate(sort[0]):
                    if s == 'server':
                        order_by.append('s.name {}'.format('DESC' if sort[1][i] else 'ASC'))
                    else:
                        order_by.append('q.{} {}'.format(s, 'DESC' if sort[1][i] else 'ASC'))

            # Build query
            query = """
                SELECT s.name AS 'server', q.query_text, q.db, q.user, q.host, q.first_seen, q.last_seen, q.last_execution_time, q.max_execution_time, q.avg_execution_time, q.count
                FROM monitoring_queries q
                JOIN monitoring m ON m.server_id = q.server_id AND m.user_id = {}
                JOIN servers s ON s.id = q.server_id {}
                WHERE 1=1 {}
                ORDER BY {}
                LIMIT 1000
            """.format(user['id'], filter_server, ' '.join(filters_values), ', '.join(order_by))

            # Execute query
            return self._sql.execute(query, (values))
