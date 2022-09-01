"""
Helper functions for mpris-dbus-apps 
"""

import re
from enum import IntEnum


def to_microsecs(time_str: str) -> int:
    """Converts time specified by the string HH:MM:SS into microseconds.

    Arguments
    time_str is a string.  The maximum value is 99:59:59. The minimum value is 00:00:00
    Returns
    An interger value of the converted time in microseconds
    """

    # Setup the regex expression that will validate the time format
    m = re.search("^[0-9][0-9]:[0-5][0-9]:[0-5][0-9]$", time_str)
    if m is None:
        raise ValueError(
            "Invalid time format. The valid format is HH:MM:SS."
            "The maximum value is 99:59:59."
            "The minimum value is 00:00:00"
        )
    parts = time_str.split(":")
    int_parts = [int(s) for s in parts]
    hours, mins, secs = int_parts
    total_mins = (hours * 60) + mins
    mins_in_microsecs = total_mins * 60000000
    total_microsecs = mins_in_microsecs + (secs * 1000000)
    return total_microsecs


def to_HHMMSS(microsecs: int) -> str:
    """Converts time specifed in microseconds to HH:MM:SS time format.
    The maximum input value is 359999000000, which is equvalent to
    99:59:59 in HH:MM:SS format.

    Arguments
    microsecs is an integer, -ve input values are converted to +ve values
    Returns a string in HH:MM:SS time format.
    """

    abs_microsecs = abs(microsecs)
    if abs_microsecs > 359999000000:
        raise ValueError("Max absolute value of microsecs is 359999000000")
    total_secs = int(abs_microsecs / 1000000)
    total_minutes = int(total_secs / 60)
    left_over_secs = total_secs % 60
    hours = int(total_minutes / 60)
    minutes = int(total_minutes % 60)
    seconds = left_over_secs
    sec_s = f"{seconds}" if seconds > 9 else f"0{seconds}"
    min_s = f"{minutes}" if minutes > 9 else f"0{minutes}"
    hr_s = f"{hours}" if hours > 9 else f"0{hours}"
    return f"{hr_s}:{min_s}:{sec_s}"


class Direction(IntEnum):
    FORWARD = 1
    REVERSE = -1
