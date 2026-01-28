from __future__ import annotations

import json
import os
import time
from datetime import datetime, time


# see issue: https://github.com/shner-elmo/TradingView-Screener/issues/12
def format_technical_rating(rating: float) -> str:
    if rating >= 0.5:
        return 'Strong Buy'
    elif rating >= 0.1:
        return 'Buy'
    elif rating >= -0.1:
        return 'Neutral'
    elif rating >= -0.5:
        return 'Sell'
    # elif x >= -0.1:
    else:
        return 'Strong Sell'

def is_current_time_between(start_hour, end_hour):
    current_time = datetime.now().time()
    start_time = time(start_hour, 0)
    end_time = time(end_hour, 0)

    return start_time <= current_time <= end_time

def get_current_time():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')