import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseService:
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def create_user(self, telegram_id: str, employee_id: str, name: str, 
                   redmine_url: str, api_key: str, project_id: str = None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users 
                    (telegram_id, employee_id, name, redmine_url, api_key, default_project_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (telegram_id) 
                    DO UPDATE SET 
                        employee_id = EXCLUDED.employee_id,
                        name = EXCLUDED.name,
                        redmine_url = EXCLUDED.redmine_url,
                        api_key = EXCLUDED.api_key,
                        default_project_id = EXCLUDED.default_project_id,
                        updated_at = CURRENT_TIMESTAMP
                """, (telegram_id, employee_id, name, redmine_url, api_key, project_id))
    
    def get_user_by_telegram_id(self, telegram_id: str):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM users WHERE telegram_id = %s
                """, (telegram_id,))
                return cur.fetchone()
    
    def get_user_by_employee_id(self, employee_id: str):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM users WHERE employee_id = %s
                """, (employee_id,))
                return cur.fetchone()
    
    def update_user(self, telegram_id: str, **kwargs):
        if not kwargs:
            return
        
        set_clause = ', '.join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE users 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = %s
                """, values)
    
    def delete_user(self, telegram_id: str):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM users WHERE telegram_id = %s
                """, (telegram_id,))