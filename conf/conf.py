import json
from datetime import time, timedelta


def __load() -> dict:
    with open('conf/conf.json') as f:
        return json.load(f)


def timings() -> dict:
    return __load()['timings']


def start_time() -> time:
    data = timings()['start']
    return time(hour=data['hour'], minute=data['minute'], second=0)


def end_time() -> time:
    data = timings()['end']
    return time(hour=data['hour'], minute=data['minute'], second=0)


def max_duration() -> timedelta:
    data = timings()['max_class_duration']
    return timedelta(days=0, hours=data['hour'], minutes=data['minute'])


def get_service_coefficients() -> dict:
    return __load()['service_coefficients']
