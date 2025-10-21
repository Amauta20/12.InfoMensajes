from app.db.database import get_db_connection

_settings_cache = {}

def get_setting(key):
    """Retrieves a setting from the database or cache."""
    if key in _settings_cache:
        return _settings_cache[key]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    value = row['value'] if row else None
    _settings_cache[key] = value # Cache the retrieved value
    return value

def set_setting(key, value):
    """Saves a setting to the database and updates the cache."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()
    _settings_cache[key] = str(value) # Update the cache with the new value

def get_pre_notification_offset():
    """Retrieves the global pre-notification offset in minutes."""
    offset = get_setting("pre_notification_offset_minutes")
    return int(offset) if offset else 15 # Default to 15 minutes

def set_pre_notification_offset(minutes):
    """Saves the global pre-notification offset in minutes."""
    set_setting("pre_notification_offset_minutes", minutes)

def get_timezone():
    """Retrieves the configured timezone name."""
    tz = get_setting("timezone")
    return tz if tz else "UTC" # Default to UTC

def set_timezone(tz_name):
    """Saves the configured timezone name."""
    set_setting("timezone", tz_name)

def get_datetime_format():
    """Retrieves the configured datetime format string."""
    dt_format = get_setting("datetime_format")
    return dt_format if dt_format else "%Y-%m-%d %H:%M:%S" # Default format

def set_datetime_format(dt_format):
    """Saves the configured datetime format string."""
    set_setting("datetime_format", dt_format)

def get_date_format():
    """Retrieves the configured date format string."""
    d_format = get_setting("date_format")
    return d_format if d_format else "%Y-%m-%d" # Default format

def set_date_format(d_format):
    """Saves the configured date format string."""
    set_setting("date_format", d_format)

def get_time_format():
    """Retrieves the configured time format string."""
    t_format = get_setting("time_format")
    return t_format if t_format else "%H:%M" # Default format

def set_time_format(t_format):
    """Saves the configured time format string."""
    set_setting("time_format", t_format)

def get_pomodoro_duration():
    duration = get_setting("pomodoro_duration")
    return int(duration) if duration else 25

def set_pomodoro_duration(duration):
    set_setting("pomodoro_duration", duration)

def get_short_break_duration():
    duration = get_setting("short_break_duration")
    return int(duration) if duration else 5

def set_short_break_duration(duration):
    set_setting("short_break_duration", duration)

def get_long_break_duration():
    duration = get_setting("long_break_duration")
    return int(duration) if duration else 15

def set_long_break_duration(duration):
    set_setting("long_break_duration", duration)

def get_todo_color():
    """Retrieves the color for 'To Do' status."""
    color = get_setting("todo_color")
    return color if color else "#FF0000"  # Default to red

def set_todo_color(color):
    """Saves the color for 'To Do' status."""
    set_setting("todo_color", color)

def get_inprogress_color():
    """Retrieves the color for 'In Progress' status."""
    color = get_setting("inprogress_color")
    return color if color else "#FFFF00"  # Default to yellow

def set_inprogress_color(color):
    """Saves the color for 'In Progress' status."""
    set_setting("inprogress_color", color)

def get_done_color():
    """Retrieves the color for 'Done' status."""
    color = get_setting("done_color")
    return color if color else "#00FF00"  # Default to green

def set_done_color(color):
    """Saves the color for 'Done' status."""
    set_setting("done_color", color)
