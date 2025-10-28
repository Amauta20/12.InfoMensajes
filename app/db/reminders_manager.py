import datetime
from app.utils import time_utils

class RemindersManager:
    def __init__(self, conn):
        self.conn = conn

    def create_reminder(self, text, due_at):
        """Creates a new reminder."""
        cursor = self.conn.cursor()
        due_at_utc_str = time_utils.to_utc(due_at).isoformat() if isinstance(due_at, datetime.datetime) else due_at
        cursor.execute(
            "INSERT INTO reminders (text, due_at) VALUES (?, ?)",
            (text, due_at_utc_str)
        )
        self.conn.commit()
        new_id = cursor.lastrowid
        return new_id

    def get_all_reminders(self):
        """Retrieves all reminders, ordered by due date."""
        reminders = self.conn.execute("SELECT id, text, due_at, is_completed FROM reminders ORDER BY due_at ASC").fetchall()
        return reminders

    def get_actual_due_reminders(self):
        """Retrieves all due and not notified reminders."""
        cursor = self.conn.cursor()
        now_utc = time_utils.to_utc(datetime.datetime.now()).isoformat()
        cursor.execute("SELECT id, text, due_at, pre_notified_at FROM reminders WHERE due_at <= ? AND is_completed = 0 AND is_notified = 0", (now_utc,))
        reminders = []
        for row in cursor.fetchall():
            reminder = dict(row)
            if reminder['due_at']:
                utc_dt = datetime.datetime.fromisoformat(reminder['due_at'])
                reminder['due_at'] = time_utils.from_utc(utc_dt).isoformat()
            reminders.append(reminder)
        return reminders

    def get_pre_due_reminders(self, pre_notification_offset_minutes):
        """Retrieves reminders that are due within the pre-notification offset and have not been pre-notified."""
        cursor = self.conn.cursor()
        now = datetime.datetime.now()
        now_utc = time_utils.to_utc(now)
        pre_due_time_utc = now_utc + datetime.timedelta(minutes=pre_notification_offset_minutes)

        now_str = now_utc.isoformat()
        pre_due_time_str = pre_due_time_utc.isoformat()

        cursor.execute("SELECT id, text, due_at FROM reminders WHERE due_at > ? AND due_at <= ? AND is_completed = 0 AND pre_notified_at IS NULL", (now_str, pre_due_time_str))
        reminders = []
        for row in cursor.fetchall():
            reminder = dict(row)
            if reminder['due_at']:
                utc_dt = datetime.datetime.fromisoformat(reminder['due_at'])
                reminder['due_at'] = time_utils.from_utc(utc_dt).isoformat()
            reminders.append(reminder)
        return reminders

    def update_reminder(self, reminder_id, text=None, due_at=None, is_completed=None, is_notified=None, pre_notified_at=None):
        """Updates a reminder."""
        cursor = self.conn.cursor()
        updates = []
        params = []
        if text is not None:
            updates.append("text = ?")
            params.append(text)
        if due_at is not None:
            due_at_utc_str = time_utils.to_utc(due_at).isoformat() if isinstance(due_at, datetime.datetime) else due_at
            updates.append("due_at = ?")
            params.append(due_at_utc_str)
        if is_completed is not None:
            updates.append("is_completed = ?")
            params.append(is_completed)
        if is_notified is not None:
            updates.append("is_notified = ?")
            params.append(is_notified)
        if pre_notified_at is not None:
            pre_notified_at_utc_str = time_utils.to_utc(pre_notified_at).isoformat() if isinstance(pre_notified_at, datetime.datetime) else pre_notified_at
            updates.append("pre_notified_at = ?")
            params.append(pre_notified_at_utc_str)

        if updates:
            params.append(reminder_id)
            cursor.execute(f"UPDATE reminders SET {', '.join(updates)} WHERE id = ?", tuple(params))
            self.conn.commit()

    def delete_reminder(self, reminder_id):
        """Deletes a reminder."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        self.conn.commit()

    def get_reminders_due_between(self, start_date, end_date):
        """Retrieves reminders with a due date between the given dates."""
        reminders = self.conn.execute("SELECT text, due_at FROM reminders WHERE due_at BETWEEN ? AND ?", (start_date, end_date)).fetchall()
        return reminders