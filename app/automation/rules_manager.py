import json
import logging

class RulesManager:
    def __init__(self, conn):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def get_all_rules(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM rules")
        return [dict(row) for row in cursor.fetchall()]

    def add_rule(self, name, trigger_type, action_type, action_params):
        try:
            params_json = json.dumps(action_params)
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO rules (name, trigger_type, action_type, action_params, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (name, trigger_type, action_type, params_json))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error adding rule: {e}")
            return None

    def update_rule(self, rule_id, name, trigger_type, action_type, action_params, is_active):
        try:
            params_json = json.dumps(action_params)
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE rules 
                SET name = ?, trigger_type = ?, action_type = ?, action_params = ?, is_active = ?
                WHERE id = ?
            """, (name, trigger_type, action_type, params_json, is_active, rule_id))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating rule: {e}")
            return False

    def delete_rule(self, rule_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting rule: {e}")
            return False

    def evaluate_trigger(self, trigger_type, context=None):
        """
        Evaluates active rules for a given trigger type.
        Returns a list of actions to be executed.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM rules WHERE trigger_type = ? AND is_active = 1", (trigger_type,))
        rules = [dict(row) for row in cursor.fetchall()]
        
        actions_to_execute = []
        for rule in rules:
            try:
                params = json.loads(rule['action_params'])
                actions_to_execute.append({
                    'type': rule['action_type'],
                    'params': params,
                    'rule_name': rule['name']
                })
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON params for rule {rule['id']}")
        
        return actions_to_execute
