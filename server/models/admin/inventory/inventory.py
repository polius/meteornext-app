class Inventory:
    def __init__(self, sql):
        self._sql = sql

    def get_groups(self):
        query = "SELECT id, name FROM groups ORDER BY name"
        return self._sql.execute(query)

    def get_users(self, group_id):
        query = "SELECT id, username FROM users WHERE group_id = %s ORDER BY username"
        return self._sql.execute(query, (group_id))
