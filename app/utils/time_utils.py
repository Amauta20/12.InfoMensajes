import datetime
from zoneinfo import ZoneInfo
from PyQt6.QtCore import QDateTime, Qt, QTimeZone
from app.db.settings_manager import SettingsManager # Changed import

def get_current_timezone():
    """Returns the configured timezone as a ZoneInfo object."""
    tz_name = SettingsManager.get_instance().get_timezone() # Use singleton
    return ZoneInfo(tz_name)

def to_utc(dt_obj: datetime.datetime) -> datetime.datetime:
    """Converts a timezone-aware datetime object to UTC."""
    if dt_obj.tzinfo is None:
        # Assume local timezone if not timezone-aware
        local_tz = datetime.datetime.now().astimezone().tzinfo
        dt_obj = dt_obj.replace(tzinfo=local_tz)
    return dt_obj.astimezone(ZoneInfo("UTC"))

def from_utc(dt_obj: datetime.datetime) -> datetime.datetime:
    """Converts a UTC datetime object to the configured local timezone."""
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=ZoneInfo("UTC"))
    return dt_obj.astimezone(get_current_timezone())

def qdatetime_from_datetime(dt_obj: datetime.datetime) -> QDateTime:
    """Converts a datetime object to a timezone-aware QDateTime object."""
    if dt_obj.tzinfo is None:
        # Assume local timezone if not timezone-aware
        local_tz = datetime.datetime.now().astimezone().tzinfo
        dt_obj = dt_obj.replace(tzinfo=local_tz)

    # Convert to the configured local timezone
    local_dt = dt_obj.astimezone(get_current_timezone())

    # Create QDateTime from local_dt components
    qdt = QDateTime(local_dt.year, local_dt.month, local_dt.day,
                    local_dt.hour, local_dt.minute, local_dt.second,
                    local_dt.microsecond // 1000, Qt.TimeSpec.LocalTime.value)
    
    # Set the correct QTimeZone
    qdt.setTimeZone(QTimeZone(get_current_timezone().key.encode()))
    return qdt

def datetime_from_qdatetime(qdt_obj: QDateTime) -> datetime.datetime:
    """Converts a QDateTime object to a timezone-aware datetime object."""
    # Ensure the QDateTime object has a timezone
    if qdt_obj.timeZone().isValid():
        # Convert QDateTime to UTC, then to Python datetime, then to configured timezone
        utc_qdt = qdt_obj.toUTC()
        dt_obj = datetime.datetime(utc_qdt.date().year(), utc_qdt.date().month(), utc_qdt.date().day(),
                                   utc_qdt.time().hour(), utc_qdt.time().minute(), utc_qdt.time().second(),
                                   utc_qdt.time().msec() * 1000, tzinfo=ZoneInfo("UTC"))
        return dt_obj.astimezone(get_current_timezone())
    else:
        # If QDateTime is not timezone-aware, assume it's in the configured local timezone
        # and convert it to a timezone-aware datetime object
        dt_obj = datetime.datetime(qdt_obj.date().year(), qdt_obj.date().month(), qdt_obj.date().day(),
                                   qdt_obj.time().hour(), qdt_obj.time().minute(), qdt_obj.time().second(),
                                   qdt_obj.time().msec() * 1000, tzinfo=get_current_timezone())
        return dt_obj

def get_current_qdatetime() -> QDateTime:
    """Returns the current time as a timezone-aware QDateTime object in the configured local timezone."""
    now_local = datetime.datetime.now(get_current_timezone())
    return qdatetime_from_datetime(now_local)

def format_datetime(dt_obj: datetime.datetime) -> str:
    """Formats a datetime object into a string using the configured datetime format."""
    return dt_obj.strftime(SettingsManager.get_instance().get_datetime_format()) # Use singleton

def convert_strftime_to_qt_format(strftime_format: str) -> str:
    """Converts a Python strftime format string to a Qt QDateTime format string.
    This is a simplified conversion for common formats.
    """
    qt_format = strftime_format
    qt_format = qt_format.replace("%Y", "yyyy")
    qt_format = qt_format.replace("%m", "MM")
    qt_format = qt_format.replace("%d", "dd")
    qt_format = qt_format.replace("%H", "HH")
    qt_format = qt_format.replace("%M", "mm")
    qt_format = qt_format.replace("%S", "ss")
    qt_format = qt_format.replace("%I", "hh") # 12-hour clock
    qt_format = qt_format.replace("%p", "AP") # AM/PM
    # Add more conversions as needed
    return qt_format

def get_week_start_end():
    """Returns the start and end of the current week."""
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    return start_of_week, end_of_week
