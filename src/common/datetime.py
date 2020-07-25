from datetime import date, datetime, timedelta, time


days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


class InvalidFormat(Exception):
    def __init__(self, msg):
        Exception.__init__(msg)


def convertToDate(dateString):
    """
    Converts strings in the following formats to date objects:
        - Monday: The previous monday (or any other day of the week)
        - Today: Today's date
        - Yesterday: Yesterday's date
        - JUN 22: The given month and date of the current year.
        - JUN 22, 2019: The given month, date, and year.
    """

    if isinstance(dateString, date):
        return dateString

    dateString = dateString.upper()

    today_d = date.today()

    if dateString == "TODAY":
        return today_d

    elif dateString == "YESTERDAY":
        return today_d - timedelta(days=1)

    elif dateString in days:
        if days.index(dateString) == today_d.weekday():
            day_diff = 7
        else:
            day_diff = (today_d.weekday() - days.index(dateString)) % 7
        return today_d - timedelta(days=day_diff)

    elif dateString.split()[0] in months:
        chunks = dateString.split()
        m = months.index(chunks[0])
        d = int(chunks[1].strip(","))
        if len(chunks) == 3:
            y = int(chunks[2])
        else:
            y = today_d.year
        return date(year=y, month=m, day=d)

    else:
        raise InvalidFormat(f"{dateString} is not a valid date format.")

def convertToTime(timeString):
    """
    Converts times that are in the form "8:30 PM" into time objects.
    """

    if isinstance(timeString, time):
        return timeString

    t = timeString.split()[0]
    if len(t) == 4:
        timeString = "0" + timeString

    return datetime.strptime(timeString, "%I:%M %p").time()

def combineDateAndTime(dateObj, timeObj):
    """Combines a date object and a time object into a datetime object"""
    return datetime.combine(dateObj, timeObj)