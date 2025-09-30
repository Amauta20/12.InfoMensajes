from app.db.database import get_db_connection
import datetime
from app.utils import time_utils

def create_reminder(text, due_at):
    """Creates a new reminder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # The due_at is already an ISO string with timezone from the dialog
    cursor.execute(
        "INSERT INTO reminders (text, due_at) VALUES (?, ?)",
        (text, due_at)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_all_reminders():
    """Retrieves all reminders, ordered by due date."""
    conn = get_db_connection()
    reminders = conn.execute("SELECT id, text, due_at, is_completed FROM reminders ORDER BY due_at ASC").fetchall()
    conn.close()
    return reminders

def get_actual_due_reminders():
    """Retrieves all due and not notified reminders."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_utc = time_utils.to_utc(datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT id, text, due_at, pre_notified_at FROM reminders WHERE due_at <= ? AND is_completed = 0 AND is_notified = 0", (now_utc,))
    reminders = []
    for row in cursor.fetchall():
        reminder = dict(row)
        if reminder['due_at']:
            utc_dt = datetime.datetime.fromisoformat(reminder['due_at'])
            reminder['due_at'] = time_utils.from_utc(utc_dt).isoformat()
        reminders.append(reminder)
    conn.close()
    return reminders

def get_pre_due_reminders(pre_notification_offset_minutes):
    """Retrieves reminders that are due within the pre-notification offset and have not been pre-notified."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now()
    now_utc = time_utils.to_utc(now)
    pre_due_time_utc = now_utc + datetime.timedelta(minutes=pre_notification_offset_minutes)

    now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")
    pre_due_time_str = pre_due_time_utc.strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT id, text, due_at FROM reminders WHERE due_at > ? AND due_at <= ? AND is_completed = 0 AND pre_notified_at IS NULL", (now_str, pre_due_time_str))
    reminders = []
    for row in cursor.fetchall():
        reminder = dict(row)
        if reminder['due_at']:
            utc_dt = datetime.datetime.fromisoformat(reminder['due_at'])
            reminder['due_at'] = time_utils.from_utc(utc_dt).isoformat()
        reminders.append(reminder)
    conn.close()
    return reminders

def update_reminder(reminder_id, text=None, due_at=None, is_completed=None, is_notified=None, pre_notified_at=None):
    """Updates a reminder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if text is not None:
        cursor.execute("UPDATE reminders SET text = ? WHERE id = ?", (text, reminder_id))
    if due_at is not None:
        # Convert due_at to UTC before storing
        due_at_utc = time_utils.to_utc(datetime.datetime.fromisoformat(due_at)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE reminders SET due_at = ? WHERE id = ?", (due_at_utc, reminder_id))
    if is_completed is not None:
        cursor.execute("UPDATE reminders SET is_completed = ? WHERE id = ?", (is_completed, reminder_id))
    if is_notified is not None:
        cursor.execute("UPDATE reminders SET is_notified = ? WHERE id = ?", (is_notified, reminder_id))
    if pre_notified_at is not None:
        cursor.execute("UPDATE reminders SET pre_notified_at = ? WHERE id = ?", (pre_notified_at, reminder_id))
    conn.commit()
    conn.close()

def delete_reminder(reminder_id):
    """Deletes a reminder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def get_reminders_due_between(start_date, end_date):
    """Retrieves reminders with a due date between the given dates."""
    conn = get_db_connection()
    reminders = conn.execute("SELECT text, due_at FROM reminders WHERE due_at BETWEEN ? AND ?", (start_date, end_date)).fetchall()
    conn.close()
    return reminders