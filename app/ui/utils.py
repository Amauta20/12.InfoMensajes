from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

def convert_utc_to_local(utc_timestamp_str):
    if not utc_timestamp_str:
        return "N/A"
    try:
        # Handle multiple possible formats, including with milliseconds
        if '.' in utc_timestamp_str:
            utc_dt = datetime.strptime(utc_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        else:
            utc_dt = datetime.strptime(utc_timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        # Get local timezone dynamically
        local_tz = datetime.now().astimezone().tzinfo
        local_dt = utc_dt.astimezone(local_tz)
        
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return utc_timestamp_str # Return original string if parsing fails

def format_timestamp_to_local_display(timestamp_str):
    if not timestamp_str:
        return "N/A"
    try:
        # Assuming timestamp_str is in YYYY-MM-DD HH:MM:SS format (from DB)
        if '.' in timestamp_str:
            utc_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
        else:
            utc_dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        # Get local timezone dynamically
        local_tz = datetime.now().astimezone().tzinfo
        local_dt = utc_dt.astimezone(local_tz)
        
        return local_dt.strftime('%d/%m/%Y %H:%M')
    except (ValueError, TypeError):
        return timestamp_str # Return original string if parsing fails