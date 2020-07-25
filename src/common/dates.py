from datetime import date, datetime, timedelta


days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

def convertToDate(dateString):
    """
    Converts strings in the following formats to date objects:
        - Monday: The previous monday (or any other day of the week)
        - Today: Today's date
        - Yesterday: Yesterday's date
        - JUN 22: The given month and date of the current year.
        - JUN 22, 2019: The given month, date, and year.
    """
    dateString = dateString.upper()

    today_d = date.today()

    if dateString == "TODAY":
        return today_d

    elif dateString == "YESTERDAY":
        return today_d - timedelta(days=1)

    elif dateString in days:
        return today_d - timedelta(days=(today_d.weekday() - days.index(dateString)) % 7)

    elif dateString.split()[0] in months:
        m = dateString.split()[0]