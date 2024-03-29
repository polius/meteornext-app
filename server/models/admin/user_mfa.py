from datetime import datetime

class User_MFA:
    def __init__(self, sql):
        self._sql = sql

    def get(self, data):
        query = "SELECT * FROM user_mfa WHERE user_id = %s"
        return self._sql.execute(query, (data['user_id']))

    def enable_2fa(self, data):
        self.disable_mfa(data)
        query = """
            INSERT INTO user_mfa (user_id, 2fa_hash, created_at)
            VALUES (%s, %s, %s)
        """
        self._sql.execute(query, (data['user_id'], data['2fa_hash'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def enable_webauthn(self, data):
        self.disable_mfa(data)
        query = """
            INSERT INTO user_mfa (user_id, webauthn_pub_key, webauthn_credential_id, webauthn_sign_count, webauthn_rp_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self._sql.execute(query, (data['user_id'], data['webauthn_pub_key'], data['webauthn_credential_id'], data['webauthn_sign_count'], data['webauthn_rp_id'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    def put_webauthn_sign_count(self, data):
        query = """
            UPDATE user_mfa
            SET webauthn_sign_count = %s
            WHERE user_id = %s
        """
        self._sql.execute(query, (data['webauthn_sign_count'], data['user_id']))

    def disable_mfa(self, data):
        query = "DELETE FROM user_mfa WHERE user_id = %s"
        self._sql.execute(query, (data['user_id']))
