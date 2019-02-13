import json
import os
import time
from datetime import datetime

import CoreLocation

from auto_mode import suntime

cmd = "osascript -e 'tell application \"System Events\" to " \
    "tell appearance preferences to set dark mode to {}'"


def set_dark_mode():
    os.system(cmd.format('true'))


def set_light_mode():
    os.system(cmd.format('false'))


def data_cache(fun):
    DATA_PATH = '/tmp/auto-switch'

    def inner():
        try:
            with open(DATA_PATH, 'r') as f:
                data = json.load(f)
                if time.time() - data['ts'] < 3600 * 24:
                    return data['lat'], data['lon']
        except FileNotFoundError:
            data = {'ts': time.time(), 'lon': 0, 'lat': 0}

        lat, lon = fun()
        if lat is None:
            if data['lat'] and data['lon']:
                return data['lat'], data['lon']
            return 0, 0

        with open(DATA_PATH, 'w') as f:
            data['lat'] = lat
            data['lon'] = lon
            json.dump(data, f)
        return lat, lon
    return inner


@data_cache
def get_coordinates():
    manager = CoreLocation.CLLocationManager.alloc().init()
    manager.delegate()
    manager.startUpdatingLocation()

    for _ in range(10):
        if CoreLocation.CLLocationManager.authorizationStatus() != 3 or \
           manager.location() is None:
            time.sleep(.1)
    else:
        return None, None

    coord = manager.location().coordinate()
    return coord.latitude, coord.longitude


def main():
    lat, lon = get_coordinates()

    sunrise = suntime.get_local_sunrise_time(lat, lon)
    sunset = suntime.get_local_sunset_time(lat, lon)
    now = datetime.now(sunset.tzinfo)

    if now > sunset:
        set_dark_mode()
    elif now > sunrise:
        set_light_mode()


if __name__ == '__main__':
    main()
