from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# Determine local timezone once at module level
_local_tz = datetime.now().astimezone().tzinfo
