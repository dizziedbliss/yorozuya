from datetime import datetime
import requests


def timestamp_to_days_ago(timestamp):
    if not timestamp:
        return None
    dt= datetime.fromisoformat(timestamp)
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    return diff.days
