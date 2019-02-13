import datetime
import math

from dateutil import tz


class SunTimeException(Exception):
    pass


def get_local_sunrise_time(lat, lon, date=None, local_time_zone=tz.tzlocal()):
    """
    Get sunrise time for local or custom time zone.
    :param lat: Latitude
    :param lon: Longitude
    :param date: Reference date. Today if not provided.
    :param local_time_zone: Local or custom time zone.
    :return: Local time zone sunrise datetime
    """
    date = datetime.date.today() if date is None else date
    sr = _calc_sun_time(lat, lon, date, True)
    if sr is None:
        raise SunTimeException(
            'The sun never rises on this location (on the specified date)')
    else:
        return sr.astimezone(local_time_zone)


def get_local_sunset_time(lat, lon, date=None, local_time_zone=tz.tzlocal()):
    """
    Get sunset time for local or custom time zone.
    :param lat: Latitude
    :param lon: Longitude
    :param date: Reference date
    :param local_time_zone: Local or custom time zone.
    :return: Local time zone sunset datetime
    """
    date = datetime.date.today() if date is None else date
    ss = _calc_sun_time(lat, lon, date, False)
    if ss is None:
        raise SunTimeException(
            'The sun never sets on this location (on the specified date)')
    else:
        return ss.astimezone(local_time_zone)


def _calc_sun_time(lat, lon, date, isRiseTime=True, zenith=90.8):
    """
    Calculate sunrise or sunset date.
    :param lat: Latitude
    :param lon: Longitude
    :param date: Reference date
    :param isRiseTime: True if you want to calculate sunrise time.
    :param zenith: Sun reference zenith
    :return: UTC sunset or sunrise datetime
    :raises: SunTimeException when there is no sunrise and sunset on given
    location and date
    """
    # isRiseTime == False, returns sunsetTime
    day = date.day
    month = date.month
    year = date.year

    TO_RAD = math.pi/180.0

    # 1. first calculate the day of the year
    N1 = math.floor(275 * month / 9)
    N2 = math.floor((month + 9) / 12)
    N3 = (1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3))
    N = N1 - (N2 * N3) + day - 30

    # 2. convert the longitude to hour value and calculate an approximate time
    lngHour = lon / 15

    if isRiseTime:
        t = N + ((6 - lngHour) / 24)
    else:  # sunset
        t = N + ((18 - lngHour) / 24)

    # 3. calculate the Sun's mean anomaly
    M = (0.9856 * t) - 3.289

    # 4. calculate the Sun's true longitude
    L = M + (1.916 * math.sin(TO_RAD*M)) + \
        (0.020 * math.sin(TO_RAD * 2 * M)) + 282.634
    L = _force_range(L, 360)  # NOTE: L adjusted into the range [0,360)

    # 5a. calculate the Sun's right ascension

    RA = (1/TO_RAD) * math.atan(0.91764 * math.tan(TO_RAD*L))
    RA = _force_range(RA, 360)  # NOTE: RA adjusted into the range [0,360)

    # 5b. right ascension value needs to be in the same quadrant as L
    Lquadrant = (math.floor(L/90)) * 90
    RAquadrant = (math.floor(RA/90)) * 90
    RA = RA + (Lquadrant - RAquadrant)

    # 5c. right ascension value needs to be converted into hours
    RA = RA / 15

    # 6. calculate the Sun's declination
    sinDec = 0.39782 * math.sin(TO_RAD*L)
    cosDec = math.cos(math.asin(sinDec))

    # 7a. calculate the Sun's local hour angle
    cosH = (math.cos(TO_RAD*zenith) - (sinDec * math.sin(TO_RAD*lat))
            ) / (cosDec * math.cos(TO_RAD*lat))

    if cosH > 1:
        # The sun never rises on this location (on the specified date)
        return None
    if cosH < -1:
        # The sun never sets on this location (on the specified date)
        return None

    # 7b. finish calculating H and convert into hours

    if isRiseTime:
        H = 360 - (1/TO_RAD) * math.acos(cosH)
    else:  # setting
        H = (1/TO_RAD) * math.acos(cosH)

    H = H / 15

    # 8. calculate local mean time of rising/setting
    T = H + RA - (0.06571 * t) - 6.622

    # 9. adjust back to UTC
    UT = T - lngHour
    UT = _force_range(UT, 24)   # UTC time in decimal format (e.g. 23.23)

    # 10. Return
    hr = _force_range(int(UT), 24)
    min = round((UT - int(UT))*60, 0)
    if min == 60:
        hr += 1
        min = 0

    # 11. check corner case https://github.com/SatAgro/suntime/issues/1
    if hr == 24:
        hr = 0
        day += 1

    return datetime.datetime(year, month, day, hr, int(min), tzinfo=tz.tzutc())


def _force_range(v, _max):
    # force v to be >= 0 and < max
    if v < 0:
        return v + _max
    elif v >= _max:
        return v - _max
    return v
