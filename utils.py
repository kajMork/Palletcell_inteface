from datetime import datetime, timezone
def get_datetime():
    """Returns the current date and time following the ISO 8601 standard, with the timezone set to UTC and the seconds precision.

    Returns:
        str: time and date in ISO 8601 format
        
    >>> print(get_datetime())
    
    """
    # Returns the current date and time following the ISO 8601 standard, with the timezone set to UTC and the seconds precision.
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


if __name__ == "__main__":
    import doctest
    doctest.testmod()