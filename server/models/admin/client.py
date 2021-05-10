from datetime import datetime

class Client:
    def __init__(self, sql):
        self._sql = sql

    def get(self, data):
        if len(list(data.keys())) == 0:
            query = """
                SELECT cq.date, u.username AS 'user', s.name AS 'server', cq.database, cq.query, cq.status, cq.records, cq.elapsed, cq.error
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN servers s ON s.id = cq.server_id
                ORDER BY cq.id DESC
                LIMIT 1000
            """
            return self._sql.execute(query)
        else:
            matching = {
                'equal': '= %s', 
                'not_equal': '!= %s', 
                'starts': "LIKE '%s%%'", 
                'not_starts': "NOT LIKE '%s%%",
                'contains': "LIKE '%%%s%%'", 
                'not_contains': "NOT LIKE '%%%s%%",
            }
            user = server = database = query = status = date_from = date_to = ''
            args = []
            if 'user' in data and len(data['user']) > 0:
                user = 'AND u.username = %s'
                args.append(data['user'])
            if 'server' in data and len(data['server']) > 0:
                server = 'AND s.name = %s'
                args.append(data['server'])
            if 'database' in data and len(data['database']) > 0 and 'databaseFilter' in data and data['databaseFilter'] in matching:
                database = f"AND cq.database {data['databaseFilter']}"
                args.append(data['database'])
            if 'query' in data and len(data['query']) > 0 and 'queryFilter' in data and data['queryFilter'] in matching:
                database = f"AND cq.query {data['queryFilter']}"
                args.append(data['query'])
            if 'status' in data and len(data['status']) > 0:
                status = 'AND cq.status = %s'
                args.append(data['status'])
            if 'dateFrom' in data and len(data['dateFrom']) > 0:
                date_from = 'AND cq.date >= %s'
                args.append(data['dateFrom'])
            if 'dateTo' in data and len(data['dateTo']) > 0:
                date_to = 'AND cq.date <= %s'
                args.append(data['dateTo'])

            query = """
                SELECT cq.date, u.username AS 'user', s.name AS 'server', cq.database, cq.query, cq.status, cq.records, cq.elapsed, cq.error
                FROM client_queries cq
                JOIN users u ON u.id = cq.user_id
                JOIN servers s ON s.id = cq.server_id
                WHERE 1=1
                {} {} {} {} {} {} {}
                ORDER BY cq.id DESC
                LIMIT 1000
            """.format(user, server, database, query, status, date_from, date_to)
            return self._sql.execute(query, args)

    def getUsers(self):
        query = "SELECT username FROM users ORDER BY username"
        return [i['username'] for i in self._sql.execute(query)]

