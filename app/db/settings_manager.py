import hashlib

class SettingsManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise Exception("SettingsManager singleton not initialized")
        return cls._instance

    @classmethod
    def initialize(cls, conn):
        if cls._instance is None:
            cls._instance = cls(conn)

    def __init__(self, conn):
        if self.__class__._instance is not None:
            raise Exception("This class is a singleton! Use get_instance() to get the instance.")
        self.conn = conn
        self._settings_cache = {} # Internal cache

    def get_setting(self, key):
        """Retrieves a setting from the database or cache."""
        if key in self._settings_cache:
            return self._settings_cache[key]

        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        value = row['value'] if row else None
        self._settings_cache[key] = value # Cache the retrieved value
        return value

    def set_setting(self, key, value):
        """Saves a setting to the database and updates the cache."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()
        self._settings_cache[key] = str(value) # Update the cache with the new value

    def get_pre_notification_offset(self):
        """Retrieves the global pre-notification offsets in minutes."""
        days = self.get_pre_notification_offset_days()
        hours = self.get_pre_notification_offset_hours()
        minutes = self.get_pre_notification_offset_minutes()
        
        offsets = []
        if days > 0:
            offsets.append(days * 24 * 60)
        if hours > 0:
            offsets.append(hours * 60)
        if minutes > 0:
            offsets.append(minutes)
            
        return offsets

    def get_pre_notification_offset_days(self):
        """Retrieves the pre-notification offset in days."""
        offset = self.get_setting("pre_notification_offset_days")
        return int(offset) if offset else 1 # Default to 1 day

    def set_pre_notification_offset_days(self, days):
        """Saves the pre-notification offset in days."""
        self.set_setting("pre_notification_offset_days", days)

    def get_pre_notification_offset_hours(self):
        """Retrieves the pre-notification offset in hours."""
        offset = self.get_setting("pre_notification_offset_hours")
        return int(offset) if offset else 1 # Default to 1 hour

    def set_pre_notification_offset_hours(self, hours):
        """Saves the pre-notification offset in hours."""
        self.set_setting("pre_notification_offset_hours", hours)

    def get_pre_notification_offset_minutes(self):
        """Retrieves the global pre-notification offset in minutes."""
        offset = self.get_setting("pre_notification_offset_minutes")
        return int(offset) if offset else 15 # Default to 15 minutes

    def set_pre_notification_offset_minutes(self, minutes):
        """Saves the global pre-notification offset in minutes."""
        self.set_setting("pre_notification_offset_minutes", minutes)

    def get_timezone(self):
        """Retrieves the configured timezone name."""
        tz = self.get_setting("timezone")
        return tz if tz else "UTC" # Default to UTC

    def set_timezone(self, tz_name):
        """Saves the configured timezone name."""
        self.set_setting("timezone", tz_name)

    def get_datetime_format(self):
        """Retrieves the configured datetime format string."""
        dt_format = self.get_setting("datetime_format")
        return dt_format if dt_format else "%Y-%m-%d %H:%M:%S" # Default format

    def set_datetime_format(self, dt_format):
        """Saves the configured datetime format string."""
        self.set_setting("datetime_format", dt_format)

    def get_date_format(self):
        """Retrieves the configured date format string."""
        d_format = self.get_setting("date_format")
        return d_format if d_format else "%Y-%m-%d" # Default format

    def set_date_format(self, d_format):
        """Saves the configured date format string."""
        self.set_setting("date_format", d_format)

    def get_time_format(self):
        """Retrieves the configured time format string."""
        t_format = self.get_setting("time_format")
        return t_format if t_format else "%H:%M" # Default format

    def set_time_format(self, t_format):
        """Saves the configured time format string."""
        self.set_setting("time_format", t_format)

    def get_pomodoro_duration(self):
        duration = self.get_setting("pomodoro_duration")
        return int(duration) if duration else 25

    def set_pomodoro_duration(self, duration):
        self.set_setting("pomodoro_duration", duration)

    def get_short_break_duration(self):
        duration = self.get_setting("short_break_duration")
        return int(duration) if duration else 5

    def set_short_break_duration(self, duration):
        self.set_setting("short_break_duration", duration)

    def get_long_break_duration(self):
        duration = self.get_setting("long_break_duration")
        return int(duration) if duration else 15

    def set_long_break_duration(self, duration):
        self.set_setting("long_break_duration", duration)

    def get_todo_color(self):
        """Retrieves the color for 'To Do' status."""
        color = self.get_setting("todo_color")
        return color if color else "#FF0000"  # Default to red

    def set_todo_color(self, color):
        """Saves the color for 'To Do' status."""
        self.set_setting("todo_color", color)

    def get_inprogress_color(self):
        """Retrieves the color for 'In Progress' status."""
        color = self.get_setting("inprogress_color")
        return color if color else "#FFFF00"  # Default to yellow

    def set_inprogress_color(self, color):
        """Saves the color for 'In Progress' status."""
        self.set_setting("inprogress_color", color)

    def get_done_color(self):
        """Retrieves the color for 'Done' status."""
        color = self.get_setting("done_color")
        return color if color else "#00FF00"  # Default to green

    def set_done_color(self, color):
        """Saves the color for 'Done' status."""
        self.set_setting("done_color", color)

    # --- Application Lock Settings ---
    def set_app_lock_password_hash(self, password_hash: str):
        """Saves the SHA256 hash of the application lock password."""
        self.set_setting("app_lock_password_hash", password_hash)

    def get_app_lock_password_hash(self) -> str | None:
        """Retrieves the SHA256 hash of the application lock password."""
        return self.get_setting("app_lock_password_hash")

    def set_app_lock_enabled(self, enabled: bool):
        """Saves whether the application lock is enabled."""
        self.set_setting("app_lock_enabled", str(enabled))

    def get_app_lock_enabled(self) -> bool:
        """Retrieves whether the application lock is enabled."""
        enabled_str = self.get_setting("app_lock_enabled")
        return enabled_str == "True" if enabled_str is not None else False

    # --- AI Provider Settings ---
    def get_ai_provider(self) -> str | None:
        """Retrieves the name of the configured AI provider."""
        return self.get_setting("ai_provider")

    def set_ai_provider(self, provider_name: str):
        """Saves the name of the configured AI provider."""
        self.set_setting("ai_provider", provider_name)

    def get_ai_model(self) -> str | None:
        """Retrieves the name of the configured AI model."""
        return self.get_setting("ai_model")

    def set_ai_model(self, model_name: str):
        """Saves the name of the configured AI model."""
        self.set_setting("ai_model", model_name)
