class Inventory:
    def __init__(self, sql):
        self._sql = sql

    def get_groups(self):
        query = "SELECT id, name FROM `groups` ORDER BY name"
        return self._sql.execute(query)

    def get_users(self, group_id=None):
        if group_id is None:
            query = """
                SELECT u.id, u.username, g.name AS 'group'
                FROM users u
                JOIN `groups` g ON g.id = u.group_id
                ORDER BY u.username
            """
            return self._sql.execute(query)
        else:
            query = "SELECT id, username FROM users WHERE group_id = %s ORDER BY username"
            return self._sql.execute(query, (group_id))

    def exist_group(self, group_id):
        query = "SELECT EXISTS(SELECT * FROM `groups` WHERE id = %s) AS exist"
        return self._sql.execute(query, (group_id))[0]['exist'] == 1
    
    def exist_user(self, group_id, user_id):
        query = "SELECT EXISTS(SELECT * FROM users WHERE id = %s AND group_id = %s) AS exist"
        return self._sql.execute(query, (user_id, group_id))[0]['exist'] == 1
