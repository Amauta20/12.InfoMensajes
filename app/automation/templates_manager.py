import logging
from datetime import datetime

class TemplatesManager:
    def __init__(self, conn):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def get_all_templates(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM templates ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def add_template(self, title, content, category="General"):
        try:
            created_at = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO templates (title, content, category, created_at)
                VALUES (?, ?, ?, ?)
            """, (title, content, category, created_at))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error adding template: {e}")
            return None

    def update_template(self, template_id, title, content, category):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE templates 
                SET title = ?, content = ?, category = ?
                WHERE id = ?
            """, (title, content, category, template_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating template: {e}")
            return False

    def delete_template(self, template_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting template: {e}")
            return False
